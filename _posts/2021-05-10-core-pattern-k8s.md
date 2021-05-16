---
layout: post
title: Changing `core_pattern` in k8s
---

If you've deployed your application on k8s and if you rely on the core dump your application generates, then I'm sure you'll scoff if it so happens that your core dump is not accessible all of a sudden.

# core_pattern
A `core_pattern` by the way is a pattern which defines the name and path for the core dump file. A core dump file is generated when a program receives certain signals. It contains an image of the process's memory at the time of termination. You'll almost never use it directly but will pass it to a debugger (GDB) to inspect the program and to potentially successfully figure out why the program died. Most commonly it's a segmentation fault hinting that your program tried to access an "unreachable" memory location.

# core_pattern and k8s
If you're running your application on containers deployed using Kubernetes, `/proc` of the underlying machine is mounted onto the containers with certain masks and the fact that it's read only. This means our `core_pattern` would be propogated from the host's `/proc/sys/kernel/core_pattern` to our containers for our applications to refer to. Now this might not be a problem if, by default, the core_pattern doesn't route the core dump to certain debugging or monitoring programs like how Ubuntu does with [apport](https://wiki.ubuntu.com/Apport).

But if whatever machine you're containers are deployed on does route the core dump to another application or has a pattern which includes specifiers like timestamp or TID, PID or hostname or a combination of all those, it becomes tedious to parse. Besides, if you're running a container, you're pretty much isolating the application's access to some extent and for that same reason, you'd want a core dump to be generated in the current working directory and be done with.

I faced this issue recently with our application deployed on GCP when the GKE cluster upgraded to a newer available version. This update broke our application which relied on a core dump to be generated in the current working directory. It was the dreaded `core_pattern` being [changed](https://github.com/kubernetes/kubernetes/pull/86329/files).

Multiple solutions sprung, first and foremost being somehow being able to configure the node pool for the nodes to come up with the updated `core_pattern`, a init script of sorts but turns out that isn't possible with GKE right now. While GCP supports configuring certain kernel [options](https://cloud.google.com/kubernetes-engine/docs/how-to/node-system-config), it doesn't support `core_pattern` attribute as of [now](https://cloud.google.com/kubernetes-engine/docs/how-to/node-system-config#sysctl-options).

# DaemonSets or InitContainers
Upon searching a little more for a possible workaround of the same, I came across a few Github issues which suggested using a DaemonSet or an InitContainer on your application Deployment resource to invoke the sysctl command before your application runs.

With a DaemonSet, you make sure as soon a new node comes up, you're going to run the `sysctl` command to update the `core_pattern` like so:

{% highlight yaml linenos %}
apiVersion: "apps/v1"
kind: "DaemonSet"
metadata:
  name: "sysctl-corepattern"
  namespace: "default"
spec:
  selector:
    matchLabels:
      app: sysctl-corepattern
  template:
    metadata:
      labels:
        app: "sysctl-corepattern"
    spec:
      containers:
        - name: "sysctl"
          image: "busybox:latest"
          resources:
            limits:
              cpu: 10m
              memory: 10Mi
          securityContext:
            privileged: true
          command:
            - "/bin/sh"
            - "-c"
            - sysctl -w kernel.core_pattern=core.%e.%p.%t && sleep 365d
{% endhighlight %}

You've to make sure the container is run in privileged mode([caution](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/)). We're also using the busybox image and we have a nominal amount of resources being allocated to the container. The command simpy updates the core pattern and _sleeps_ for long long time. Why? DaemonSets are meant to run daemons or long-running programs which are essential to your application's functioning. If your daemon exits, it is restarted which in our case would be pointless. So we update the config and let it sleep.

If you don't quite like the idea of the hack above, you can run your sysctl command in an InitContainer as part of the DaemonSet like so:

{% highlight yaml linenos %}
apiVersion: "apps/v1"
kind: "DaemonSet"
metadata:
  name: "sysctl-corepattern"
  namespace: "default"
spec:
  selector:
    matchLabels:
      app: sysctl-corepattern
  template:
    metadata:
      labels:
        app: "sysctl-corepattern"
    spec:
      initContainers:
        - name: "sysctl"
          image: "busybox:latest"
          securityContext:
            privileged: true
          command:
            - "/bin/sh"
            - "-c"
            - sysctl -w kernel.core_pattern=core.%e.%p.%t
      containers:
        - name: pause
          image: gcr.io/google_containers/pause
          resources:
            limits:
              cpu: 10m
              memory: 50Mi
            requests:
              cpu: 10m
              memory: 50Mi
{% endhighlight %}

Here, we're doing the same thing but in an initContainer. Note that we're using the [pause](https://github.com/qzchenwl/google-containers/blob/master/pause-amd64/pause:latest) image as an equivalent of `sleep 365d` from the previous example. Now the pause container is meant to be used as a container which keeps the pod retain it's network setup. Normally when all the containers in a pod die, the network namespace dies and is setup from scratch. Pause keeps the network setup in place while the main/appliation container restarts. Pause, in fact, does nothing but sleeps until it receives a particular signal. Refer to the [man page](https://man7.org/linux/man-pages/man2/pause.2.html) and the [source](https://github.com/kubernetes/kubernetes/blob/a45aeb626c7f2303c49466ae52833cd410cf88f2/build/pause/linux/pause.c).

I don't prefer this version since it's just another version of sleep hack albeit a little more sophisticated.

The last approach that I came across was to run an initContainer as part of the Deployment:

{% highlight yaml linenos %}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
  labels:
    app: nginx
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      initContainers:
        - name: "sysctl"
          image: "busybox:latest"
          securityContext:
            privileged: true
          command:
            - "/bin/sh"
            - "-c"
            - sysctl -w kernel.core_pattern=core.%e.%p.%t
      containers:
      - name: nginx
        image: nginx:1.14.2
        ports:
        - containerPort: 80
{% endhighlight %}

Ok, that's exactly the same as the one with the DaemonSet but you get the idea.

There are a few problems with this approach though:

1. You wouldn't want to slow down your application start up time by making it run the initContainer first which would in turn involve pulling the image if it's not already present on the node.
2. You don't want the sysctl command to run for every pod that ends up on that node, just running it once would've sufficed but this would make it run for every single pod coming up on every node. No thanks.
3. Finally, if you're running an application which handles data at scale. You're most certainly are or have optimized for auto scaling and with that, you're not going to willingly add additional overhead to your infrastructure (i.e. the previous two points).

# Conclusion
I ended up using the first approach i.e. DaemonSet with sysctl and a sleep since If you're anyways going to use a hack, try to keep it simple for the sake of readability and maintainability. I would've loved to have `linuxConfig` support changing this configuration on the node level so as to prevent that extra set of resources being hogged on a sleep.

---
