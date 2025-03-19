---
layout: post
date: 2020-07-24
title: Introduction to runc
---

We've been using runc at work in production for a while now and although it seemed somewhat obscure at first, we've come around to being used to it so much so that it seems more intuitive than docker. I wanted to write this blogpost as a gentle introduction to runc for folks who want to try it out. This blogpost will try to serve as a quick primer on getting started with runc i.e. managing a container lifecycle with runc.

## Introduction
runc is a lightweight portable container runtime parts of which were internally used by Docker and were packaged as a single binary and released as an open source project under the the Open Containers Initiative (OCI) as a way of giving back to the community[1]. Explained simply, runc is a lightweight tool written in Go which helps manage a container's lifecycle i.e creating, running, killing and deleting a container. You'll go through each of these steps in this post and see how runc differs from Docker when it comes to running containers.

You'll work with the official golang docker image as a running example for the purpose of this article. You can find more details about this image on [Docker Hub](https://hub.docker.com/_/golang).

## Requirements
Unlike docker, runc doesn't abstract tedious tasks under the hood and rather expects you to arrange whatever is it that is required for it to work. Let's run through the requirements:

### runc Binary
runc is a portable piece of software, for GNU/Linux users, it's as simple as fetching the binary and giving execute permissions to it in order to work with runc:

```
$ curl -L -o /usr/bin/runc https://github.com/opencontainers/runc/releases/download/v1.0.0-rc10/runc.amd64 && chmod +x /usr/bin/runc
```

You can head over to the project's [release page](https://github.com/opencontainers/runc) to download other versions. It's also worth noting that runc doesn't work on macOS so if you are on a Mac, your best bet is to run runc inside a docker container.

### runtime-spec
Specifying configuration options such as volume mounts, memory limits or uid:gid mapping while running a container with docker is as simple as specifying command line options to the docker command. While using runc, these configurations are passed to runc as a file. This configuration file, the runtime-spec, is a configuration standard put in place by the Open Container Initiative (OCI) to specify options for a container and is used by runc[2]. In simpler words, the runtime-spec is a JSON file named `config.json` consisting of configurations pertaining to a specific container.

You'll go through a few attributes in the runtime-spec in this post to get enough understanding so as to be able to run containers. Later sections will focus on attributes which require further explanation. Consider this sample runtime-spec snippet:

```
{
	"ociVersion": "1.0.1-dev",
	"process": {
		"terminal": true,
		"user": {
			"uid": 0,
			"gid": 0
		},
		"args": [ "sh" ],
		"env": [
			"PATH=/usr/local/bin/
			"TERM=xterm"
		],
		"cwd": "/",
		"capabilities": { ... },
		"rlimits": [{ ... }],
		"noNewPrivileges": true
	},
    ...
}
```

runc expects the configuration file in the exact same format with a certain required fields and a few other optional ones. You might have figured out a few options from the snippet above alone for instance, the environment variables, the current working directory and the uid:gid mapping. There are other configuration options which give you more control over how the container should perform that you'll go through in the sections to follow.

### Root filesystem
This is exactly what it sounds like, root filesystem for the container. There are multiple ways you can get hold of a root filesystem from a Docker image but the easiest and the one advised by the OCI is using `docker export`:

```
$ docker export $(docker create golang) | tar -C rootfs -xvf -
```

This will generate the unarchived root filesystem for our golang docker image which you'll now use to create containers using runc.

Now that you've gathered up the required prerequisites, you can now go ahead and run containers using runc.

## Running a container
Before running the container, you've to make sure you have all the prerequisites in the required manner. The `runc` binary, by default, looks for the root filesystem and the runtime-spec in a directory which is referred to as a "bundle". The bundle directory must have the runtime-spec(config.json) and the root filesystem(rootfs) in order for runc to work.

```
~/golang
.
├── config.json
└── rootfs/
      ├── home/
      ├── tmp/
      ├── ..
      └── ..
```

As shown above, having such a directory, you'll be able to run runc commands in the `~/golang` directory for it to work appropriately.

With that out of the way, you can go ahead and create the container:

```
$ runc create golang

# list active containers
$ runc list
ID              PID         STATUS      BUNDLE          CREATED                        OWNER
golang          39          created     ~/golang        2020-04-12T14:23:46.7358607Z   root

# starts running the user-defined command inside the container
$ runc start golang

$ runc list
ID              PID         STATUS      BUNDLE          CREATED                        OWNER
golang          39          running     ~/golang        2020-04-12T14:23:46.7358607Z   root

# creates and starts the container
$ runc run -d golang
$ runc list
ID              PID         STATUS      BUNDLE          CREATED                        OWNER
golang          39          running     ~/golang        2020-04-12T14:26:46.7358607Z   root
```

Contrary to the title of this section, there are multiple commands to "spin up" a container using runc. In the snippet above, we used the following commands:

- `create`: creates an instance of the container from the bundle but it doesn't run the command specified as an entrypoint in the runtime-spec(config.json).
- `start`: runs the init command(specified in the runtime-spec) for a created container. This essentially means your container is now "running". Your application or whatever command you're running inside the container can now respond to requests or do the job you intend it to do.
- `run`: it creates and starts the container. Passing a `-d` will run the container in detached mode. You'll be using this command more frequently than individually creating and then starting the container.
- `list`: lists containers you've created, they could be running, paused, stopped or in created state. (not an exhaustive list of states). This is most useful to inquire about the current status of the containers that you've started or stopped with runc.

You can now "spin up" containers with runc, killing or deleting containers with runc is also fairly straightforward.

## Stopping a container
Once you've started the container and played around with it, you need to discard it in such a manner that it does not run in the background holding onto resources or populating your pid tables for virtually no reason.

Although there's no `stop` command provided by runc, the `runc kill` command, when run without any options, sends a `SIGTERM` signal to the init process of the container thereby stopping the container. This moves the container to a `stopped` state. Your container might still be holding on to certain resources used by processes contained by your container though. As a side not, while you're at the topic of killing of processes inside containers, it's worthwhile to go through issues associated with handling of [zombie processes in docker](https://blog.phusion.nl/2015/01/20/docker-and-the-pid-1-zombie-reaping-problem/).

The `runc delete` command frees up any resources that a container is holding on to thereby completely removing the container. You won't be able to inspect this container in any way (checking filesystem or otherwise), and it will not show up when you do `runc list`.

```
# creates and starts the container
$ runc run -d golang
$ runc list
ID              PID         STATUS      BUNDLE          CREATED                        OWNER
golang          39          running     ~/golang        2020-04-12T14:26:46.7358607Z   root

$ runc kill golang
$ runc list
ID              PID         STATUS      BUNDLE          CREATED                        OWNER
golang          39          stopped     ~/golang        2020-04-12T14:26:46.7358607Z   root

$ runc delete golang
$ runc list
```

You've sent a signal to a running container and then released any resources held by that container in stopped state to completely "stop it". Read more about additional options you can use with these commands by running `runc <command> --help`.

You can now manage a container using runc, you'll take it one step further and see how you can checkpoint/restore a container with runc.

## Checkpoint/Restore a container
Similar to docker, runc provides a handy functionality to checkpoint/restore running containers. You can think of checkpointing a container as serializing the state of a running process and then storing the contents on disk. This serialized blob has all the metadata required to restore the process to the same point from when it was checkpointed at a later point in time. That's an extremely simplified explanation of how criu works. It's a lot more complex than it sounds but it's adequate for the purpose of this article.

To accomplish this, runc uses `criu`, an open source piece of software which does the actual checkpoint and restore. In order to use runc commands such as `checkpoint` and `restore`, you ought to have the criu binary installed on your host system. You can find instruction for installing criu [here](https://github.com/checkpoint-restore/criu).

```
# run the container in detached mode
$ runc run -d golang
$ runc list
ID              PID         STATUS      BUNDLE          CREATED                        OWNER
golang          39          running     ~/golang        2020-04-12T14:26:46.7358607Z   root

$ runc checkpoint golang

$ runc restore golang
$ runc list
ID              PID         STATUS      BUNDLE          CREATED                        OWNER
golang          39          running     ~/golang        2020-04-12T14:26:46.7358607Z   root
```
In the above snippet, you checkpoint the golang container while it was running. When you checkpoint a container, `criu` stores the checkpoint metadata in the current directory. You can restore the golang container to the same state it was in at the time of checkpoint at any later point in time. You've to make sure that the files created by criu are not modified in any way whatsoever.

This might not be readily clear as to why or how this would be useful but there are cases when such a functionality can help you improve your workflow, some of the usecases I can think of are:

- If container startup time is something that's holding you back i.e. If you have a container in which the init process takes time to startup. You can start the container, let the server come up and running, checkpoint the container and then just keep on restoring the container. You are essentially discarding the inital overhead of waiting for the init process to be ready. A common candidate for this could be your database servers.
- If you are running your application in an environment in which CPU/Memory usage is a critical metric, it would help to keep the checkpointed container on the filesystem and restore it right before serving a request, might be useful for jobs which need to run at intervals while maintaining internal state both in memory and disk.

There might be other more sophisticated use cases but I think checkpoint/restore is a great way to save up on time and resources depending upon the requirements.

You can, apart from managing a container lifecycle, also do things like checkpoint/restore. It's imperative to focus on the runtime-spec now as it is what controls how the container is run, what resources it gets and other configuration options.

## runtime-spec
The runtime spec, as discussed above, is a set of configuration options stored in a file read by runc to apply configuration before running the container. In docker, you can explicitly set some of the options that you can provide in the runtime-spec. Going through the most common configuration options, you can:

- Limit the amount of memory that can be allocated to the processes running under the new cgroup inside the container. For instance, the snippet below will instruct runc to limit the amount of memory available to the container to 2068MB. A value of `-1` means unlimited memory.
```
"memory": {
    "limit": 2168455168,
    "swap": 2168455168,
    "kernel": -1
}
```

- Apply limits on a per-process basis, for instance, you can limit the number of open file descriptors that a process can open. You can specify all the rlimits here, refer to the [official manpage](https://linux.die.net/man/2/setrlimit) for an exhaustive list.
```
"rlimits": [
    {
        "type": "RLIMIT_NOFILE",
        "hard": 1024,
        "soft": 1024
    }
]
```

- Control the number of processes that can run inside your container. If applied, the following will limit the number of processes to just 1024. This can be crucial if you're running code from untrusted vendors because they can very well turn into a fork-bomb and you might end up losing your container. On the flipside, don't go overboard with this limit, almost all the programs uses fork/exec to start subprocesses and limiting those could end up hampering your container's functionality.
```
"pids": {
    "limit": 1024
}
```

- Allow the rootfs to be readonly or not. With the following configuration, the rootfs of the container will be readonly i.e. no writes would be allowed:
```
"root": {
    "path": "rootfs",
    "readonly": true
}
```

- Run processes in the container as a different user:group. The following snippet runs the container as user `101` and group `201`. If you're doing this, also make sure to check if you need to give your container `setuid` and `setgid` capabilities.
```
"user": {
    "uid": 101,
    "gid": 201
}
```

- You can, like Docker, mount volumes from the host to the container. The following mounts `/home/Documents/images` from the host to the container at `/mnt/images` with read and write permissions:
```
"mounts": [
    {
        "destination": "/mnt/images",
        "type": "bind",
        "source": "/home/Documents/images",
        "options": [
            "rbind",
            "rw"
        ]
    }
]
```

There are lots of other configuration options in the runtime-spec that you can use to configure your container as per your requirements. It would not be wise to discuss them all here for the sake of brevity and keeping this post relevant. You can head over to runtime-spec's [Github repo](https://github.com/opencontainers/runtime-spec) for all the options available.

## Conclusion
You learnt how to manage a container's lifecycle using runc, a lightweight, portable container runtime. It is highly unlikely you'll use runc to manage containers on a daily basis, docker is much more user friendly and convenient for that especially when you factor in the added time and effort to gather the pre-requisites for runc to do it's job. On the other hand, runc can prove to fill in gaps Docker can't, these can vary from performance to the lack of additional, often unnecessary features built into docker that runc doesn't come bundled with. But those are decisions for you to take a call on. Anyhow, it's always a good idea to learn something new just for the fun of it.

If you found something in this article that's incorrectly stated or can be improved, feel free to [raise a PR](https://github.com/danishprakash/danishprakash.github.io/tree/master/_posts) or contact me.

## References
1. [https://www.docker.com/blog/runc]()
2. [https://github.com/opencontainers/runtime-spec/blob/master/spec.md]()
