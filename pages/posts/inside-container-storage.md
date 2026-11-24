---
layout: post
date: 2026-11-14
title: "Inside Container Storage: From Image Layers To Running Containers"
---

Doing `podman pull` followed by `podman run` is a pretty common pattern if you've worked with containers. But there's a lot going on under the hood just between those two commands. In this article, we'll try to bridge the gap between a container image on your local machine to the root filesystem for a running container. The idea, as always, is to have a _slightly_ better understanding of what goes behind these seemingly simple set of commands.

## Background

But let's first understand what we're trying to do here. When you run the command `podman run <image>`, podman [pulls](/posts/build-a-container-registry-from-scratch) the base image if not present, arranges the various layers of the image, creates a root filesystem, and runs a container off of it.

We'll do something similar--we'll take a container image, and hack together a virtual filesystem that we can use as a root filesystem for a hand-wrangled container. By hand-wrangled, I mean we'll also create a simple container without using a container runtime, mostly using existing Linux primitives such as namespaces, `mount`, `pivot_root`, etc.

### Example Image

For this article, since our starting point is a container image in our local filesystem, we'll use the following [Containerfile](/posts/dockerfile-practices) to base our image on:

```
FROM docker.io/library/alpine:latest
RUN echo "written by layer 2" > /etc/motd
RUN rm /etc/issue
```

We're basing our image on the Alpine image. The Alpine image has, among other files, two files that we'll modify for demonstration purposes in this article. We first overwrite the existing message of the day with "written by layer 2" string into `/etc/motd` and then we remove the `/etc/issue` file. They both are unrelated but they will be used to illustrate two different concepts in the sections ahead.

### Interlude -- _Image Layers_

Before we go any further, it's imperative that we [understand what an image really is](/posts/build-a-container-image-from-scratch). An image primarily consists of layers, configs, manifests, and sometimes, an image index. These components and their structures are defined by the [OCI Image Spec](https://github.com/opencontainers/image-spec).

For the purposes of this post, we need to worry about layers. A layer is a filesystem changeset. It's a diff between two filesystems serialized as a tar archive. Consider our Containerfile again:

```
FROM docker.io/library/alpine:latest
RUN echo "written by layer 2" > /etc/motd
RUN rm /etc/issue
```

Here, the base Alpine image gives us the first layer: a complete root filesystem. Every `RUN` instruction after that creates a new layer. A new layer does not copy the filesystem, it only records what the instruction changed.

The second layer comes from `RUN echo "written by layer 2" > /etc/motd`. The command modified one file, `/etc/motd`. So this layer is a tar archive with just one entry: the modified `/etc/motd` file. The original `/etc/motd` from the base layer still exists but the second layer supersedes it when the layers are used to produce the final filesystem.

Similarly, the `RUN rm /etc/issue` creates the third layer. This command deletes a file but the tar archive cannot hold a _deleted_ file. So the OCI Image Spec uses a marker that indicates a deleted file. This is called a _whiteout_ marker, generally denoted by prefixing the file with `.wh.`. And therefore, our third layer consists of just one file entry in the tar archive, `/etc/.wh.issue`. Again, the original `/etc/issue` file continues to exist in our first/base layer and this new layer with the whiteout marker hides it.

### Interlude -- _Container Storage_

While we're at it, let's also understand how and where the layers of our image are stored. Podman stores container related data on the local host filesystem. This path is referred to as _graphroot_ and is configurable via `storage.conf`, its default location is `/var/lib/containers/storage`.

```
# cd /var/lib/containers
# tree -L 2
.
├── cache
│   └── blob-info-cache-v1.sqlite
└── storage
    ├── db.sql
    ├── libpod
    ├── overlay
    ├── overlay-containers
    ├── overlay-images
    ├── overlay-layers
    ├── storage.lock
    ├── userns.lock
    └── volumes
```

Podman stores the global container state db, container details, lock files, cache files, and the image layers. If we pry further into `storage/overlay`, we can see the three layers of our image:

```
# tree -L 1 storage/overlay
storage/overlay
├── 550e8cb82a5d3b54d0f3eb59a8a344a622bc692448b9b5226dbabec016c41ca6
├── 75f1d9657d880da5f75298e8f40e9928bb6e260c50d26f97af196845307e3064
└── b3bfe80d8303374ae0356ac6dac202885897c9f82463e8497a235a9dfaa5044c
```

Layers are denoted by a sha256 checksum, for base layers, this is the checksum of their tar archive, for non-base layers, it's a checksum combination of the parent ID and other attributes. This idea of referring to an object by its content's checksum or sometimes even simply by its content is referred to as content-addressability. The filesystem changeset for each of the layers can be found in the `diff` subdirectory. For instance, expanding each of the three layers, we can identify which layer is which:

```
// Layer 1: base Alpine layer with the complete root filesystem
# ls storage/overlay/75f1d9657d880da5f75298e8f40e9928bb6e260c50d26f97af196845307e3064/diff
bin  dev  etc  home  lib  media  mnt  opt  proc  root  run  sbin  srv  sys  tmp  usr  var

// Layer 2: includes only the modified /etc/motd file
# tree -L 2 storage/overlay/550e8cb82a5d3b54d0f3eb59a8a344a622bc692448b9b5226dbabec016c41ca6/diff
storage/overlay/550e8cb82a5d3b54d0f3eb59a8a344a622bc692448b9b5226dbabec016c41ca6/diff
└── etc
    └── motd

// Layer 3: includes only the whiteout /etc/issue file
# tree -L 2 storage/overlay/b3bfe80d8303374ae0356ac6dac202885897c9f82463e8497a235a9dfaa5044c/diff
storage/overlay/b3bfe80d8303374ae0356ac6dac202885897c9f82463e8497a235a9dfaa5044c/diff
└── etc
    └── issue
```

So now we have our image (and its layers). But a container does not run directly from an image's layers. It runs from a directory, the complete root filesystem. How do we turn our image consisting of three layers into a single directory that the container can use? The answer is Overlay filesystem.

## Overlay -- _*quick primer*_

Let's assume you have one directory tree with files that you want to share with multiple processes (containers in our case) but each container is allowed to change those files. The naive solution is to make a copy for each container but this costs disk space and time.

Overlay is an implementation of Unionised filesystems. It allows you to stack multiple directory trees into one. This allows processes to use it without affecting the original directory tree. Let's try to see how this works.

Overlay uses four directories to accomplish this:

1. `lower` - One or more read-only directory trees. Since these are read-only, they can be part of other overlay mounts without any issues. This makes it possible to share a large directory or large number of files with many different processes.
2. `upper` - A read-write directory tree. When a process makes changes to a file in lower dir, it is copied into the upper and then modified, this is called **_copy-up_**.
3. `work` - This is a scratch space directory that the kernel uses to facilitate copy-up and dentry caching, among other things.
4. `merged` - The combined view of upper and lower. This is the final directory tree that abstracts the permission model, the copy-up operations, whiteout handling, etc.

Now you should be able to connect how all of this maps to containers. The `lower` directories are made up of all the different layers of a container image stacked on top of each other in the right order. When the container makes any changes to any of the files in the `lower`, overlay copy-up(s) the file to `upper` leaving the actual image layers untouched. This is what allows the same image to be shared across 100s of different containers at no additional cost.

The upper is where the container makes the changes--writing files, deleting files, etc. And merged is what you see inside the container. To the container, it feels like a seamless root filesystem but under the hood we now have a rough idea of what's really going on.

## Layers to Lowers
An attempt at a cheesy section title, but now that we have the foundational concepts out of the way, let's create the overlay mount for our container image using its three different layers. Please note that I'm using rootful containers exclusively for the purposes of this post.

For starters, let's identify the layers and assign their absolute paths to bash variables we can reuse easily and to avoid using the full checksum:

```
# ls /var/lib/containers/storage/overlay/75f1d.../diff
bin  etc   lib    mnt  proc  run   srv  tmp  var
dev  home  media  opt  root  sbin  sys  usr
# L1=/var/lib/containers/storage/overlay/75f1d.../diff

# tree /var/lib/containers/storage/overlay/550e8.../diff
etc
└── motd
# L2=/var/lib/containers/storage/overlay/550e8.../diff

# tree $L3 /var/lib/containers/storage/overlay/b3bfe.../diff
etc
└── issue
# L3=/var/lib/containers/storage/overlay/b3bfe.../diff
# stat -c '%F' $L3/etc/issue
character special file
```

So we can see the base Alpine image, denoted by `L1`, has the complete root filesystem. `L2` denotes the second layer that has the modified `/etc/motd` file, and finally, `L3` is set to the third layer in our image that has the `/etc/issue` file with the whiteout marker. If you noticed, there's no `.wh.` prefix for the `/etc/issue` file that was deleted in the third layer. This is because the OCI Image Spec and Overlay use different techniques to identify whiteouts. The OCI Image Spec requires the `.wh.` prefix we earlier talked about but it's limited to use only within an image and its distribution. Once the image is unpacked, as in the above case by Podman, the whiteout file is converted to a special character device with device number 0:0 that is recognized by Overlay as a whiteout/deleted file. This is why when you stat the file and print its file type, it says "character special file" which tells Overlay that this file is deleted and should _not_ show up in the merged view.

Of course it goes without saying that you would never find yourself having to do any of this--running across different layers to identify which is which because the container engine does this for you. We're going through this little dance here purely for instructional purposes in order to understand what Podman does for us when we run a container.

## mount -- _complete root filesystem_

Now, let's create the overlay mount. As we saw before, there are 4 directories to be created or provided to `mount` for an overlay mount. Let's set them up and create the overlay mount for our image:

```
// 2. Setup our overlay mount directories
# mkdir -p /tmp/live/{upper,merged,work}

// 3. Create the mount
# mount --type overlay overlay \
    --options lowerdir+=$L3,lowerdir+=$L2,lowerdir+=$L1 \
    --options upperdir=/tmp/live/upper \
    --options workdir=/tmp/live/work \
    /tmp/live/merged
```

We create empty `merged`, `upper`, and `work` directories in a new temporary directory `/tmp/live/`. To `mount`, we pass the three layers as `lowerdir` in order (more on this shortly). We also pass the `workdir` and finally specify the mount target as `/tmp/live/merged`. Overlay would then stack all the lower dirs, prepare the workdir and upper, and produce the complete root filesystem at `/tmp/live/merged/`.

Once mounted, we can verify that the right files from our layers show up in the final overlay mount. Below, we can see that we have the complete root filesystem from the Alpine base image. We can also note the `/etc/motd` file that we modified using `RUN echo "written by layer 2" > /etc/motd` in layer 2. Finally, we notice that in the merged view of our overlay mount, `/etc/issue` simply doesn't exist. While preparing the `merged` view, Overlay would've encountered `/etc/issue` from layer 3 that was marked as a special character device as we saw earlier, and removed it from the merged view.

```
# ls /tmp/live/merged/
bin  etc   lib    mnt  proc  run   srv  tmp  var
dev  home  media  opt  root  sbin  sys  usr

# cat /tmp/live/merged/etc/motd
written by layer 2

# stat /tmp/live/merged/etc/issue
stat: cannot statx '/tmp/live/merged/etc/issue': No such file or directory
```

### Layer ordering in Overlay

Now, if you've been following along, you'd understand that our image layers make up for the lower directories of the mount. What's important here is the order in which you specify the lower directories. When specifying multiple lower directories, they will be stacked beginning from the rightmost one and going to the left. So in our case, `$L1` which if you recall is the Alpine base image layer, will be the bottom layer, as is expected. Then we have our second layer `$L2` and finally, the top layer `$L3`. This is exactly the order of our Containerfile and the layers it generated.

Thinking about it on a higher level, the lower directories for our overlay mount have to be the final root filesystem that is the result of all three layers of our image. And as we have seen earlier, the order of the three layers is critical because layers are not copies of the directory trees, but they are _filesystem changesets_. So in our example Containerfile, the second layer overwrites the `/etc/motd` file with the string `written by layer 2`. So if we change the order of the lower directories in the mount command, it will result in defined yet unintended behaviour. To illustrate this, let's swap the order of `$L1` and `$L2` such that `$L2` is the rightmost or the bottom layer of our overlay mount.

```
# mount --type overlay overlay \
    --options lowerdir+=$L3,lowerdir+=$L1,lowerdir+=$L2 \
    --options upperdir=/tmp/live/upper \
    --options workdir=/tmp/live/work \
    /tmp/live/merged

# cat /tmp/live/merged/etc/motd
Welcome to Alpine!
...
```

As you can see, the modified `/etc/motd` file from the second layer (`$L2`) has been superseded by the original `/etc/motd` file that is part of the Alpine base layer (`$L1`). So the precedence order becomes Layer 3 > Layer 1 > Layer 2. Any changes to any files in Layer 2 will now be superseded by the vanilla root filesystem from our Alpine base image.

## Container From Scratch -- _testing our overlay mount_

We're all set with our complete root filesystem. In order to demonstrate how container runtimes make use of this, let's build a rudimentary container from first principles. We'll make it stupid simple with `unshare`, `mount`, and `pivot_root`:

```
# cd /tmp/live

# unshare \
    --mount \
    --pid \
    --fork \
    sh

# cd merged
# pivot_root . .
# umount -l .
```

Let's unpack. In order, we first cd into our overlay prep directory `/tmp/live`. Then we use `unshare` to create a new mount and PID namespace.

At this point, our shell is in its own mount namespace but its root is still the host's `/`. We need to swap it with our overlay mount. That's what `pivot_root` is doing here. With `pivot_root . .`, the kernel stacks the old root on top of the new one, at `/`, so we promptly unmount the old one with `umount` so that our overlay mount is the new root.

```
# head -n 1 /etc/os-release
NAME="Alpine Linux"

# cat /etc/motd
written by layer 2

# stat /etc/issue
stat: can't stat '/etc/issue': No such file or directory
```

Once we do that, we notice that we're _inside_ the container we built using the Alpine base image. We also see the modified `/etc/motd` and lastly, the absence of `/etc/issue` from our container.

We can also mount a proc filesystem to get closer to a real container such that `ps` reports just the processes in its namespace.

```
# mount -t proc proc /proc
# ps
PID   USER     TIME  COMMAND
    1 root      0:00 sh
    6 root      0:00 ps
```

### Making changes to files

What happens when our container makes changes to files? What happens if we create a new file? Where do they land in our overlay mount? From the Overlay primer earlier, we know that changes to the files go into upper. Let's verify that:

```
(ctr) # echo "hello" > /etc/hello
(host) # cat /tmp/live/{merged,upper}/etc/hello
hello
hello

(ctr) # echo "written by ctr" > /etc/motd
(host) # cat /tmp/live/{merged,upper}/etc/motd
written by ctr
written by ctr

(host) # head -n 1 $L{1,2,3}/etc/motd
L1: Welcome to Alpine!
L2: written by layer 2
L3: error: No such file or directory
```

### Using our overlay mount with Podman
Lastly, we can also pass the overlay mount we created directly to podman using the `--rootfs` flag. Podman accepts a complete root filesystem via this flag and uses that as the container root filesystem. The podman container sees our modified `motd` but it didn't mount anything for the root filesystem.

```
# podman run --rm --network none --rootfs /tmp/live/merged /bin/sh -c 'cat /etc/motd'
written by ctr
```

### Layer sharing
As mentioned earlier, one of the redeeming features of using the overlay filesystem for containers is sharing of container image layers across different containers.

Multiple containers of one image mount the same image layers as `lowerdir`. Each container adds its changes only to `upperdir` without modifying the `lowerdir`.

While not related to overlay, the way container images are [constructed](/posts/build-a-container-image-from-scratch), the layers themselves are shared across different images. Our Alpine base image for instance will be shared with any image that includes the same Alpine image _with_ the same content.

## What does Podman do?
What we have done so far is a fairly rudimentary and extremely simplified version of what all that podman does for you when you try to run a container off an image. Podman uses [container-libs/storage](https://github.com/podman-container-tools/container-libs/tree/main/storage) and other shared container libraries to manage the container lifecycle which includes unpacking container images, preparing overlay mounts for every container, local container store, handling container configuration among other things.

We haven't talked about persistence so far but container engines allow you to also attach volumes to your containers that act as persistent storage.

Apart from handling the layer to overlay pipeline, Podman then also builds a proper container using lower-level container runtimes such as `runc` or `crun` among many other things. See this [list](https://podman.io/features) for a comprehensive list of features supported by Podman.

## Why Overlay? Other alternatives?
It's reasonable to ask the question, why Overlay? Overlay is one of many storage drivers that you can use with Podman. Other storage drivers supported by Podman are "vfs", "btrfs", and "zfs". We chose overlay here to demonstrate that there's quite a lot that goes behind the scenes when it comes to container storage.

But then again, you can get by without choosing a storage driver. Most container engines do that for you based on certain heuristics. Alternatively, you can specify a driver priority where Podman would try all the drivers in order and choose the first driver that matches.

## Conclusion
The motivation behind writing this article, as I mentioned in the beginning, was to explain what happens between `podman pull` and `podman run`, how and where files inside your containers are stored, and how an image becomes your container's root filesystem. We know now by hand-wrangling an overlay mount that an image is a stack of read-only layers. Overlay stacks them into one directory which the container uses as its root directory. We also hacked together a contraption we called a container to demonstrate how files are read from the layer into the overlay and finally into the container. We also saw how modifications to the files are handled by overlay.

Naturally, there's a lot more complexity when it comes to container storage. As mentioned in an earlier section, we haven't covered a lot of other aspects of container storage such as security and encryption, that container engines such as podman handle for us or the additional features they provide on top of the foundational functionalities.

I hope this article provided some clarity on what container storage means in its most basic form ie layers and the container filesystem.
