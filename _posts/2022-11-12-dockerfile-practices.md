---
layout: post
title: Dockerfile Practices
---

Yet another post on the internet about how to write Dockerfiles, for the umpteenth time. But I'm writing this post as a reference for my future self rather than having it act as a gospel for others to abide by while writing Dockerfiles. That was the primary purpose, the secondary purpose is, in general, to [write more](https://danishpraka.sh/2022/01/30/year-in-review-2021.html#reading--writing). Quality over quantity somewhat. I've been slacking away from finishing up a lot of articles due to this small block that Julia Evans described quite neatly, people find it extremely difficult to write without explaining everything from the beginning.

This post doesn't follow a weighted order, it's just some of the practices I've personally used and (some) would prefer to use whenever I write Dockerfiles. This post also assumes you have a basic understanding of Docker and Dockerfiles.

# Order your layers
The lowest hanging fruit out of them all. The basic rule of thumb here is to add statements dealing with changes to your code at the very end of the file. And conversely, keep things such as installing dependencies or other prerequisites, essentially things that are not supposed to change once you've written them down, near the top.

{% highlight text linenos %}
FROM go

COPY . .

RUN apt-get update \
    && apt-get install -y psutil vim curl make gcc

RUN go build -o app
{% endhighlight %}

Based on our example, the COPY directive is going to be executed every time you change your source. And the way Docker works, all the layers below line 3 are going to be reevaluated again. Fix this by moving the COPY directive to a more appropriate place.

{% highlight text linenos %}
FROM go

RUN apt-get update \
    && apt-get install -y psutil vim curl make gcc

COPY . .
RUN go build -o app
{% endhighlight %}

<br>
# Format your Dockerfiles
Was not originally planning to add it here, but I've seen countless examples of unformatted Dockerfiles to actually include this as its own section. Unfortunately, there's no standardised formatting tool such as `gofmt` available for Dockerfiles and so it's difficult to attain a quorum during discussions or reviews but one thing I've seen that helps is to refer to official Dockerfiles or files from popular open source projects.

Some things I've gathered so far:
1. While installing packages, specify each per line for better diffs & readability.
2. Use empty lines. Group sets of instructions based on functionality.
3. Break chained commands and start the next line with an `&&`.
3. Make use of comments only if necessary.

{% highlight text linenos %}
...

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        curl \
        make \
        gcc \
        psutil \
    && rm -rf /var/lib/apt/lists/*

...
{% endhighlight %}

These are by no means definitive rules that one must follow but if you don't follow any, these can help as a good starting point. You can then take it from there.

# Discard the fluff
Pretty self-explanatory but I hardly see people following this. It could either just be an awareness issue or the fact that the ROI is not huge when it comes to cleaning up after a dependency install for example. But either way, maintaining hygiene of your codebase in general is a good practice. So, make sure you're only really installing what you need. It also reduces the surface area for potential security issues.

1. Don't install unnecessary packages that you _feel_ could come in handy. As much as I like having vim in an environment, it's just not a requirement for my Dockerfile.
2. Use `--no-install-recommends` with apt while installing packages, this tells apt to not install recommended packages along with whatever you're trying to install.
3. Clean up package manager cache. For apt for e.g. use `rm -rf /var/lib/apt/lists/*`

{% highlight text linenos %}
FROM go

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        curl \
        make \
        gcc \
        psutil \
    && rm -rf /var/lib/apt/lists/*

COPY . .
RUN make install
{% endhighlight %}

Once done installing the prerequisites, we can go ahead and build our application. Here, we're using a [Makefile](https://danishpraka.sh/2019/12/07/using-makefiles-for-go.html) target which wraps the `go install` command internally.

# Multi-stage builds!
If there's to be only one takeaway from this article, let it be this one. Docker allows you to base your docker image off of other docker images as part of a single build.

Let's say you built your application from source by installing all the prerequisites and other requirements and finally you have your binary ready for use. But you don't really need all the other dependencies you installed in your final environment. Build stages can help us define multiple stages, for instance, in this example, we can have a build stage where we build our application. We can then have a second stage which can be based off a lean alpine image and since we have access to the previous stage, we can simply copy our binary from the build stage to our final stage. Multi-stage builds allows us to properly define separation of concerns to significantly reduce the final image size.

{% highlight text linenos %}
# Stage 2; builder stage
FROM go:1.17 as builder

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        curl \
        make \
        gcc \
        psutil \
    && rm -rf /var/lib/apt/lists/*

COPY . .
RUN make install

# Stage 2
FROM alpine

COPY --from=builder /go/bin/myapp /usr/bin/myapp
{% endhighlight %}

This will give you a docker image with a small footprint and without all the extra unnecessary fluff that Go would've generated in the previous stage (think cache, artifacts etc.)

Using multi-stage builds can drastically improve both the size and hygiene of your Dockerfiles.

Multi-stage builds also serve other important purposes, for e.g. allowing you to have a dev environment build within your primary Dockerfile or allowing you to build your dependencies in parallel (concurrency pattern) resulting in faster builds.


# Use ARGs effectively
Using `ARG`s effectively can help you achieve [DRY](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself) when you write Dockerfiles. Let's say you're trying to install a 3rd party application in your Dockerfile. And to avoid any unforeseen issues in the future, you prudently make it a point of downloading a specific version of that application. Let's say we have the following hitherto:

{% highlight text linenos %}
FROM debian

RUN wget https://download.com/version=1.2.4 \
	&& tar -xzf application_1.2.4.tar \
	&& cd application_1.2.4

...
{% endhighlight %}

You can make use of an `ARG` directive here and avoid specifying the version every single time:

{% highlight text linenos %}
ARG APPLICATION_VERSION=1.2.4

FROM debian

RUN wget https://download.com/version=${APPLICATION_VERSION} \
	&& tar -xzf application_${APPLICATION_VERSION}.tar \
	&& cd application_${APPLICATION_VERSION}

...
{% endhighlight %}

This makes the Dockerfile much more readable and extensible should you need to install another version of the same package in future or any other modifications.

Now, an obvious question arises as to why can't we use `ENV` instead of `ARG` and what even is the difference between the two. One way to think about it is that ARGs are the environment variables for your build step whereas ENVs are environment variables for your container environment when you eventually run your container.

# Minimize layers
It's always better to keep as few layers as possible. Not every Dockerfile directive creates a new layer, only `RUN`, `COPY` and `ADD` create new layers. But I've come across Dockerfiles containing every single bash command in its own separate `RUN` directive. Fewer layers results in a lower size of the overall image because more number of images adds more overhead, think compressing, metadata, cache, etc.

It also allows you to build logical cacheable units, for instance, in the snippet below, that one `RUN` layer is installing CRIU which can be reused in other builds safely.

{% highlight text linenos %}
FROM debian

ARG CRIU_VERSION=3.17
RUN wget https://github.com/checkpoint-restore/criu/archive/refs/tags/v${CRIU_VERSION}.tar.gz && \
    tar xvf v${CRIU_VERSION}.tar.gz && \
    rm v${CRIU_VERSION}.tar.gz && \
    cd criu-${CRIU_VERSION} && \
    make && \
    cp ./criu/criu /usr/bin/
{% endhighlight %}

<br>
# Understand `ENTRYPOINT` and `CMD`
This is probably the most commonly misinterpreted of them all. Part of the confusion arises due to the different forms available for both `ENTRYPOINT` and `CMD`. But to keep it simple, I'm going to only consider the JSON form here while discussing a preferred way to use these two directives.

There are two common ways one would use a Docker image. They are either used as an interactive sandbox environment wherein you could exec and do some tasks. Or they are used as a binary. For instance, in our example above, we really just want to run this docker image and expect it to start our Go binary. This is the format that's commonly used when it comes to usage within container orchestration systems such as Kubernetes.

That being said, if you're using your Docker image as an executable, your Dockerfile should have either of `ENTRYPOINT` or `CMD` or preferably both. `ENTRYPOINT` defines the command that is supposed to run in your container, `CMD` specifies default arguments that are passed to the command specified by `ENTRYPOINT`. Let's understand this better with an example:

{% highlight text linenos %}
FROM debian

...

ENTRYPOINT ["ls"]
CMD ["-a", "-l"]
{% endhighlight %}

Once built, when you do `docker run <image>`, it should execute the `ls` command with the two arguments specified by `CMD`.

This is not to say that this covers the complete difference between the two directives, but it should help you make informed decisions for the most common use-cases wrt to specifying commands and arguments for your Docker image. I can maybe talk about the in-depth differences (signals, pids, etc) that arises with the usage between these two in a separate post of its own.

# Dockerignore
Having an up to date dockerignore file in your project's repository ensures no fluff is added to your Docker images and additionally, it can prevent you from accidentaly adding credentials or secret files to your Docker images. I could've added this to the discard fluff section but if implemented, it really helps maintain the hygiene of your repository, like how .gitignore helps keeps your upstream all neat and clean.

# Conclusion
This is the kind of post which doesn't really call for an inferential conclusion so instead, I'm going to quickly summarize everything we talked about in this post:
1. Order your layers with the least frequently changes on top and so on.
2. Spend time sensibly formatting your Dockerfiles.
3. Keep the image as minimal as possible, discard all fluff.
4. Use multi-stage builds as much as you can.
5. Make use of `ARG`s wherever deemed necessary.
6. Minimize the number of layers in your Docker image.
7. Understand the difference between `ENTRYPOINT` and `CMD`.
8. Use `.dockerignore` in your projects.

As mentioned previously, I've curated this list of practices from my own experience with writing Dockerfiles for the past 3 years. There is a good chance some of this runs counter against what you follow or what should be followed. And if that's the case, if you came across anything in this article that might not be right(highly likely) or if you have suggestions for improvements, feel free to report an [issue](https://github.com/danishprakash/danishpraka.sh/issues) or reach out to me directly via email.

:wq
