---
layout: post
date: 2024-05-26
title: Compile & Boot Linux Kernel with QEMU
Date: 26th May 2024
---

### Introduction
This is a quick and dirty guide for you to compile the linux kernel from scratch and boot it using QEMU. I did this recently and figured it'd make sense for me to jot it down either for my own future self or for someone else looking to do the same.

### Kernel Source
Get the kernel source, either by cloning the [git repository](https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/) or downloading the [archives](https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/refs/tags).

```
$ git clone git://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git stable
$ cd stable
```

### Kernel Config
The kernel uses a `.config` file to store the configuration settings for building the kernel. In order to build a basic configuration file, you can use the following make command:

```
$ make defconfig
*** Default configuration is based on 'x86_64_defconfig'
#
# configuration written to .config
#
```

You can inspect the build options or modify it if you're planning something specific for instance, you want to have support for a particular filesystem or adding support for a device. Next, we need to enable tmpfs support in order to load our initramfs while the kernel boots. So run the following command, which would open up a TUI allowing you to select various options..

```
$ make menuconfig
```

..and enable:
```
Device Drivers
  --> Generic Driver Options
    --> Maintain a devtmpfs filesystem to mount at /dev
```

Once done, hit Esc and save the config when asked. We can now build our configured kernel:

```
$ make -j$(nproc) bzImage
```

Depending upon your machine, it might take a couple of minutes for the build to complete. Once done, the kernel is stored in `./arch/x86_64/boot/bzImage`, let's copy that to the root of our directory:

```
$ cp arch/x86_64/boo/bzImage .
```

## Busybox
Busybox is a single small executable that provides many UNIX utilities and is intended to be used in embedded systems. For us, it will help to create a micro distribution with basic commands we can use to play around with.

```
$ wget https://busybox.net/downloads/busybox-1.36.1.tar.bz2
$ tar -xvjf busybox-1.36.1.tar.bz2
$ cd busybox-1.36.1.tar.bz2/
```

Next, we'll configure busybox..

```
$ make menuconfig
```

..and enable:
```
Settings
  --> Build statis binary (no shared libs)
```

And exit and save your config, build busybox next:

```
$ make -j$(nprocs)
$ make install
```

<span class="note">Note: If you're trying this on your host which runs Linux >=6.8, then busybox will fail to build due to https://bugs.busybox.net/show_bug.cgi?id=15931, you might have try a different host kernel version, preferably lower than 6.8.</span>

The Busybox binaries will be installed in `_install/`. We'll use them while preparing our initramfs next.

## Initramfs
We'll now create initramfs. There are tools that you can use to create the initramfs (Dracut, etc) but it's not uncommon to "hand-made" the initramfs, which is what we'll do:

```
$ mkdir initramfs
$ mkdir -p initramfs/{bin,sbin,etc,proc,sys,dev,usr/bin,usr/sbin}
$ tree initramfs
initramfs
├── bin
├── dev
├── etc
├── proc
├── sbin
├── sys
└── usr
    ├── bin
    └── sbin

10 directories, 0 files
```

Copy the busybox binaries to the respective directories:
```
$ cp -a busybox-1.36.0/_install/* initramfs
```

And then create the init script `initramfs/init` that would act as the init process:

```
#!/bin/sh

mount -t sysfs sysfs /sys
mount -t proc proc /proc
mount -t devtmpfs udev /dev

exec /bin/sh
shutdown
```

Now, create the initramfs archive:

```
$ cd initramfs
$ find . -print0 \
    | cpio --null -ov --format=newc \
    | gzip -9 > ../initramfs.cpio.gz
```

## Boot using QEMU
Now, let's boot the kernel

```
$ qemu-system-x86_64 \
    -kernel ./arch/x86/boot/bzImage \
    -nographic \
    -append "console=ttyS0" \
    -initrd initramfs.cpio.gz \
    -m 1G \
    --enable-kvm
```

This would boot the kernel within your terminal.
