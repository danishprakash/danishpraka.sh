---
layout: post
date: 2023-12-17
title: Build a Docker Image from Scratch
---

For a developer, a Container image is essentially a collection of configurations required to run a container. But what really is a container image? For the longest time, I theoretically knew what a container image was, how it was made up of layers and that it was a collection of tar archives but that was about it. I always find it easier to understand something by building or cracking open something so that's what I'm trying in this article.

# Introduction

This post aims to build a "Docker" image from scratch. This means that we're not going to use docker or any other compatible tool to build our docker image. But rather, we'll try to manually create all the files and metadata and then package it into a format that docker understands. In so doing, the idea is to see what really constitutes a docker image and how docker does it under the hood when you run `docker build -f Dockerfile` on your terminal.

We'll be creating an image based on the "scratch" base image. Don't be confused with the word "scratch" here but scratch here refers to an empty image, from Docker, used normally for building super minimal or base images. Our image is going to have a statically linked C binary which prints the string "hello world!" when run. Now, if we were to be using docker to build our image, the Dockerfile for the same would look like:

```
FROM scratch

COPY ./hello ./

ENTRYPOINT ["./hello"]
```

We base our image off of the "scratch" image we discussed above, copy our statically linked `hello` binary into the image and finally set this binary as the [entrypoint](/posts/dockerfile-practices) of the container.

Now that we know what our docker image is supposed to be doing, let's start by building one from scratch.

#### layers
Layers are the basic building blocks of an image. An image, a docker image in this case, is made up of different layers stacked on top of each other to generate the complete end image. You can also consider it a filesystem changeset i.e a diff format for filesystems for when you add or remove elements from a base filesystem. One simple way to understand this is to imagine that you're building the following image:

```
FROM alpine

COPY ./hello /root/
```

Here, your image contains 2 layers, well roughly. The first layer comes from the base image, the alpine official docker image. Almost every instruction inside your Dockerfile generates another layer. So in the above case, the `COPY` instruction creates the second layer which includes filesystem changes to the layer before it, the alpine base image. So in this case, we're copying over a file onto the base image's root filesystem.

So let's create our binary and then create an archive for it:
```
$ cat hello.c
#include <stdio.h>

int main(){
    printf("hello world\n");
    return 0;
}


$ gcc -o hello hello.c -static
$ tree
.
├── hello
└── hello.c

$ tar --remove-files -cf layer.tar hello
```

In the above, we create our static binary and create an archive which simply includes it. This constitues our layer. Also note the `--remove-files` flag that ensures files that are being created an archive of, are removed so that we don't end up having a bunch of unwanted files in our directory.

Now we have our first and only layer ready as a tar archive. Note that the archive is not zipped, but a standard archive, it's required by design. 

Docker requires all layers and the concomitant metadata to be inside a content-addressable directory. This simply means that we need to create a directory and name is at its own sha256 sum. Let's quickly do that:

```
$ sha256sum layer.tar
f0890db25e21d129985da9eb714feea4c610994ddb3ddddc974cb3404a142117 layer.tar
sum
$ mkdir f0890db25e21d129985da9eb714feea4c610994ddb3ddddc974cb3404a142117
$ mv layer.tar f0890db25e21d129985da9eb714feea4c610994ddb3ddddc974cb3404a142117/

$ tree
.
└── f0890db25e21d129985da9eb714feea4c610994ddb3ddddc974cb3404a142117
    └── layer.tar
```

We calculate the sha256 sum for our layer archive, create a directory with the sum and then move our layer inside this directory. At this point, our directory has a directory corresponding to the only layer in our image which includes the tar archive consisting of the files that are to be part of our image, the `hello` binary in this case.

Now that we have the layers required for our image ready, we can now move on to defining the configuration of the container that will run based on this image.

#### Config
When we run a container using `docker run ...`, we sometimes supply command line options such as volume mounts or commands to be run inside the container. These options can be part of the image, and often are, which are then passes onto the container engine/runtime of choice which consumes these options to configure the container as per our requirements.

Container configuration can also include options such as the environment variables to be part of the container, or the entrypoint or even the history of the layers for the image in question, which are represented via a JSON file which is then made part of the image. The only option we need to pass onto the [container engine](/posts/introduction-to-runc) in our image are:

```
$ vim config.json
{
    "config": {
        "Entrypoint": [
            "./hello"
        ]
    },
    "rootfs": {
        "type": "layers",
        "diff_ids": [
            "sha256:f0890db25e21d129985da9eb714feea4c610994ddb3ddddc974cb3404a142117"
        ]
    }
}
```
We have defined our entrypoint to be our static binary. We then refer to the layer by its content addressable name used by our image. The config file itself is also required to be content addressable, so let's do that:

```
$ sha256sum config.json
25e8b3bd9720a2c1a4c1908aaca598593fc5483f5f3ecfaa1a40aa271ef8615f config.json
$ mv config.json 25e8b3bd9720a2c1a4c1908aaca598593fc5483f5f3ecfaa1a40aa271ef8615f.json

$ tree
.
├── 25e8b3bd9720a2c1a4c1908aaca598593fc5483f5f3ecfaa1a40aa271ef8615f.json
└── f0890db25e21d129985da9eb714feea4c610994ddb3ddddc974cb3404a142117
    └── layer.tar
```

Howsoever arcane our directory might look like to us, it's completely comprehensible to docker but we've to make sure that docker finds the appropriate files in our image, let's create a file that holds that information.

#### manifest
The manifest file holds metadata such as location of the config, the different layers that are part the image and the image name or tag, etc. Docker uses a file called `manifest.json` to accomplish this:

```
$ vim manifest.json
[
    {
        "Config": "25e8b3bd9720a2c1a4c1908aaca598593fc5483f5f3ecfaa1a40aa271ef8615f.json",
        "RepoTags": [
            "hello:scratch"
        ],
        "Layers": [
            "f0890db25e21d129985da9eb714feea4c610994ddb3ddddc974cb3404a142117/layer.tar"
        ]
    }
]
```

The file above can have multiple entries for each image, in our case, we have just one image with the `scratch` tag. We refer to that image name and tag, along with the config and the layer archive our image will use.

At this point, we have the following files:
```
$ tree
.
├── f0890db25e21d129985da9eb714feea4c610994ddb3ddddc974cb3404a142117
│   └── layer.tar
├── 25e8b3bd9720a2c1a4c1908aaca598593fc5483f5f3ecfaa1a40aa271ef8615f.json
└── manifest.json
```

(in the order shown above)

1. `f0890db25e21d129985da9eb714feea4c610994ddb3ddddc974cb3404a142117` -- A directory that consists of the only layer in our image which in turn consists of a single static binary.
2. `25e8b3bd9720a2c1a4c1908aaca598593fc5483f5f3ecfaa1a40aa271ef8615f.json` -- Container configuration options such as the entrypoint and environment variables that are going to be used by the container runtime when running the container based off of our image.
3. `manifest.json` -- Metadata such as image name and tag for our image along with other data.


# Bringing it together
Now we have all the parts in place for our image. For docker to be able to load this, we need to create an archive for this whole directory could then be called the "image". Let's do that:

```
$ tree
.
├── f0890db25e21d129985da9eb714feea4c610994ddb3ddddc974cb3404a142117
│   └── layer.tar
├── 25e8b3bd9720a2c1a4c1908aaca598593fc5483f5f3ecfaa1a40aa271ef8615f.json
└── manifest.json
$ tar -cf hello.tar *

$ docker load < hello.tar
f0890db25e21: Loading layer [==================>]  3.686MB/3.686MB
Loaded image: hello:scratch

$ docker run hello:scratch
hello world
```

And would you look at that, it works as if we created the image using docker itself. Our entrypoint works as expected, we see the output from our static binary. Let's take a look at the image:

```
$ docker image ls hello
REPOSITORY   TAG       IMAGE ID       CREATED   SIZE
hello        scratch    25e8b3bd9720  N/A       3.67MB
```

Thanks to the scratch base image, our image has a minimal footprint, in fact, the only file in our image is our binary.

# Using a Base Image
Let's try creating a version of our image which is based on `alpine` rather than scratch. This would introduce another layer in our image, so let's see how multiple layers are handled or represented within the configuration and metadata. For the sake of better understanding, this is how our Dockerfile would look using alpine if we hadn't been doing it from scratch.

```
FROM alpine:latest

COPY ./hello /root/hello

ENTRYPOINT ["./hello"]
```

In our image so far, we had just one layer that consists of our `hello` binary. As we've seen before, a layer can be considered a filesystem diff. So if we plan to use alpine as our base image, we need the respective root filesystem onto which we'll base our second layer, the binary. You can obtain the alpine root filesystem from their official website.

```
$ wget https://dl-cdn.alpinelinux.org/alpine/v3.18/releases/x86_64/alpine-minirootfs-3.18.4-x86_64.tar.gz -O rootfs.tar.gz

$ tar -xvf rootfs.tar.gz
$ tar --remove-files -cf layer.tar *
```

That tar dance at the end is because, as we saw before, docker requires the layers as standard archive, and not a gzipped one. So we're unzipping the gzipped archive and then converting it again to a tar archive without compression.

Next up, let's create a new directory corresponding to our new base image layer:
```
$ sha256sum layer.tar
60319e6788a598db0914c14d8608cd4865ec12fc1f31bfaa82933c09c504a0db layer.tar
$ mkdir 60319e6788a598db0914c14d8608cd4865ec12fc1f31bfaa82933c09c504a0db
$ mv layer.tar 60319e6788a598db0914c14d8608cd4865ec12fc1f31bfaa82933c09c504a0db/

$ tree
.
├── 25e8b3bd9720a2c1a4c1908aaca598593fc5483f5f3ecfaa1a40aa271ef8615f.json
├── 60319e6788a598db0914c14d8608cd4865ec12fc1f31bfaa82933c09c504a0db
│   └── layer.tar
├── f0890db25e21d129985da9eb714feea4c610994ddb3ddddc974cb3404a142117
│   └── layer.tar
└── manifest.json
```

We'll add this new alpine image as a new tag to our existing image. Essentially, we'll have an image `hello` with two tags, `scratch` and `alpine`. We already have the former set up and running, what's left is to create a config and update the metadata to reflect the new tag `alpine`. Let's create a new config by copying over the existing one and updating the contents for it:

```
$ vim config.json
{
    "config": {
        "Entrypoint": [
            "./hello"
        ]
    },
    "rootfs": {
        "type": "layers",
        "diff_ids": [
            "sha256:60319e6788a598db0914c14d8608cd4865ec12fc1f31bfaa82933c09c504a0db",
            "sha256:f0890db25e21d129985da9eb714feea4c610994ddb3ddddc974cb3404a142117"
        ]
    }
}

$ sha256sum config.json
3d0268e9a91e466ba3a9385fe12edf4a9804089fd582fe3c79a6fa11c9db317b config.json
$ mv config.json 3d0268e9a91e466ba3a9385fe12edf4a9804089fd582fe3c79a6fa11c9db317b.json
```

We have the new config, we added the base layer as the first layer in the `diff_ids` block. Layers are represented top to bottom so our base alpine layer comes first and then our layer with the static binary. Apart from the layers, nothing else really changes, we'd still be able to tell the difference if we try to exec into the container and more readily if we simply compare the image sizes. All that's left now is to let docker know that there's a new image with a new tag, so let's update the manifest file:

```
$ vim manifest.json
[
    {
        "Config": "25e8b3bd9720a2c1a4c1908aaca598593fc5483f5f3ecfaa1a40aa271ef8615f.json",
        "RepoTags": [
            "hello:scratch"
        ],
        "Layers": [
            "f0890db25e21d129985da9eb714feea4c610994ddb3ddddc974cb3404a142117/layer.tar"
        ]
    },
    {
        "Config": "3d0268e9a91e466ba3a9385fe12edf4a9804089fd582fe3c79a6fa11c9db317b.json",
        "RepoTags": [
            "hello:alpine"
        ],
        "Layers": [
            "60319e6788a598db0914c14d8608cd4865ec12fc1f31bfaa82933c09c504a0db/layer.tar",
            "f0890db25e21d129985da9eb714feea4c610994ddb3ddddc974cb3404a142117/layer.tar"
        ]
    }
]
```

We added a new entry in the file which creates a new image named `hello:alpine` and refers to its configuration. And finally, it has a reference to the two layers archives. Let's create an archive for our new image(s) and load them up in docker:

```
$ tree
.
├── 25e8b3bd9720a2c1a4c1908aaca598593fc5483f5f3ecfaa1a40aa271ef8615f.json
├── 3d0268e9a91e466ba3a9385fe12edf4a9804089fd582fe3c79a6fa11c9db317b.json
├── 60319e6788a598db0914c14d8608cd4865ec12fc1f31bfaa82933c09c504a0db
│   └── layer.tar
├── f0890db25e21d129985da9eb714feea4c610994ddb3ddddc974cb3404a142117
│   └── layer.tar
└── manifest.json
$ tar -cf hello.tar *

$ docker load < hello.tar
f0890db25e21: Loading layer [==================>]  3.686MB/3.686MB
Loaded image: hello:scratch
Loaded image: hello:alpine

$ docker run hello:scratch
hello world
$ docker run hello:alpine
hello world

$ docker image ls hello
REPOSITORY   TAG       IMAGE ID       CREATED   SIZE
hello        scratch   25e8b3bd9720   N/A       3.67MB
hello        alpine    3d0268e9a91e   N/A       11MB
```

So there we have it, our two images loaded into the docker daemon. We can run both of them and see the same output from both of them. One interesting thing to note is the size difference between the two images. Alpine, while still having a lower footprint is larger than scratch, but nothing extraordinary. Hopefully this example demonstrated interaction between different layers in an image and how a manifest file can represent multiple images from a single file.


# Conclusion
I was initially planning to title this article "Container Image Internals" and the first draft of that came out all theoretical and while reading it, even I felt bored even though I enjoyed finding about all I could about container images for the post. But then I decided to document the fun part of this whole journey and here we are. In this article, we saw how we can "build" a docker image from scratch. But that's not to say that we'd be doing something like that on a day to day basis. You should never find yourself doing this as part of your regular development workflow. This article intentionally uses a simple example and so it misses out on more recent developments such as how this would work with the OCI spec or if I had to pry open a v1 docker image spec image, how would that differ from what we did here.

But alas, it's always fun to crack open something and to understanding things so I hope this serves as a brief primer on understanding docker image internals.  If you find anything that seems wrong or if you think there's something that can be improved, feel free to reach out. 
 
:wq
