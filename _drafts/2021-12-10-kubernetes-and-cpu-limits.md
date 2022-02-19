---
layout: post
title: Kubernetes and CPU Limits
---

I recently came across a very interesting issue concerning resource limits and how they are implemented in Kubernetes. In this blogpost, I've tried to explain the problem, the cause of the problem and potential solutions to the issue.

# The problem
I saw that a few requests were timing out for one of our workloads. This was a Deployment which was managing a few pods. Now, these timeouts would span over a few minutes and during that time, we'd also see quite a few of the pods failing their readiness and liveness probes.

The kind of workloads we were running, timeouts on certain requests at random wasn't acceptable. So we had to figure out why this was the case, even though it was just for 2 minutes that one time.

I'm also going to deliberately avoid talking about Resource Requests in this post since they are in no real way involved in the aforementioned issue.

# Resources limits
Kubernetes allows you to specify Memory and CPU limits for your workloads. Since memory is an incompressible resource, if you've specified a memory limit of 1Gb for your workloads and if your workload tries to use more than that, the system(either the container runtime or the Kernel) will terminate the process in your workload with an OOM (out of memory) error. CPU, on the other hand, is a compressible resource i.e. if you've allocated 1CPU to your workloads and if your workload is reaching that limit, your workloads will start experiencing throttling.


## Memory limits

As mentioned above, If your workloads are using more than the allocated memory limit, the process will get OOMKilled. Do note that this process [may or may not](https://github.com/kubernetes/kubernetes/issues/50632) be the init process of your container. You should be able to figure out whether you're actually experiencing an OOMKill event by going through the logs. With that, it becomes easy for you to gauge resource usage for your workloads and  to decide whether you need to increase the allocated memory.

## CPU limits

CPU Limits work in an entirely different way. Being a compressible resource, the system based on certain heuristics, will allow or disallow CPU cycles to your process if and when it comes to throttling. The apparent downside of throttling is that there's not much visibility.

The way CPU throtlling works is that the Kernel uses two configuration options

1. `cpu_period_us`: The CPU cycle interval which the schedueler uses to reset the used quota for a process. It's default value is 100ms.
2. `cpu_quota_us`: The total runtime for which the process can use the CPU in a given period before being reset.

Now, let's understand how this works. First of all, when you specify 1CPU as a limit for your workload, it means that the processes can use 1000milicore of CPU. To calculate the amount of CPU a process can use before being throttled, we can use:

{% highlight text %}
cpu_quota_us/cpu_period_us * 1000 => mili CPU
{% endhighlight %}

Let's think of the following scenarios:

- You want your process to be able to use 1 CPU completely:

{% highlight text %}
cpu_quota_us=250ms
cpu_period_us=250ms

250/250 * 1000 => 1000m => 1CPU
{% endhighlight %}

- You want your process to be able to use 20% of a CPU:

{% highlight text %}
cpu_quota_us=50ms
cpu_period_us=10ms

10/50 * 1000 => 200m => 0.2CPU
{% endhighlight %}

That seems to work well but there's a catch, if you're running in a multi-threaded environment or your pod or container (cgroup) is running multiple threads, the `cpu_quota_us` is calculated across all the threads. Which is to say, if you're running 10 threads and you've the following config:

{% highlight text %}
running 10 threads

cpu_quota_us=10ms
cpu_period_us=50ms

(10)/50 * 1000 => 200m CPU => 200

quota per threads = 10/5 => 2ms
{% endhighlight %}

This means you'll exceed your quota in 2ms and you're processed will be throttled for the remaining 48ms of that cycle. As mentioned, this is especially pronounced in multi-threaded environment and Kubernetes is a primary example. In fact, Kubernetes is the reason this issue came to light in the first place.

I'll also like to clear up what throttling means really. In the previos example, when all the threads use up the allocated quota of 10ms within a period, the scheduler will not allow the process to run until the next period. This is what throttling is in a nutshell.

To add insult to injury, there happen\[s\|ed\] to be a [bug](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=de53fd7aedb100f03e5d2231cfce0e4993282425) in various Linux kernel versions which aggravates this issue by throttling CPU for processes which are not close to their quota. This, again, is pronounced in multi-threaded environments like Kubernetes. Refer to this [gist](https://gist.github.com/bobrik/2030ff040fad360327a5fab7a09c4ff1) for a breakdown of what's going on.



# Solutions?
This issue was not hard to come by since a lot of folks started experiencing this especially when working at scale. But there was no single one-shot fix for this since there were multiple things going on. There was the obvious problem of threads using up the quota within a period. Then there's the Kernel bug which is a different beast altogether. Bottomline, you've the following options:

1. Disable CPU Limits. If there are no CPU limits on your workloads, the CFS will not come into action and the whole chaos will be averted. This has its own issues in that it's not feasible for folks to run their applications without a CPU limit. This comes down to the kind of workloads you're running.
2. Disabling CFS. This essentially disables enforcing limits but you've to go through a [different route](https://github.com/kubernetes/kubernetes/pull/63437/files) to do this.
3. Reducing the `cpu_period_us` to a lower value. The default value is 100ms which a little too high when it comes to high performance web services or other such applications. Because, the cycle is longer, the processes are throttled for longer before their quota is reset. For e.g. [Monzo](https://github.com/monzo/kubernetes/commit/9888ef89f3ae85e643f4d1098f0ba001414a5f25) added support for this in their fork of Kubernetes and have [seen good results](https://github.com/kubernetes/kubernetes/issues/51135#issuecomment-384908627).
4. Update Linux kernel. This is reserved for last for a good reason. If you're reading this, there's a high probability that you're using Kubernetes as part of a cloud offering for e.g. GKE, AKS or EKS, etc. If that's the case, it becomes extremely tedious to update the Linux kernel version on your worker node images. Even if you manage to do this, it fixes part of the problem, CPU throttling would still be there as long as you have limits.

I personally tried removing the CPU limits and it worked as expected. For others, maybe disabling the CFS is easier or just waiting out for GKE et.al to come up with node images with the updated Kernel version.

# Kubelet

But wait, there's more. Remember I mentioned in passing that the pods also faced a lot of readiness and liveness probes failing? Well, I reached out to GCP for info on that.

My hypothesis was that during such a crisis i.e. the processes getting throttled and adding to that, the CFS bug in the kernel lead to the Kubelet also being in a resource crunch and hence unable to complete probes. The kubelet being unable to performa a network request to check the container health lead to a somewhat domino effect in the cluster. Pods failing the readiness and liveness probes would trigger new pods to come up unnecessarily. At the same time, some workloads already running at max would just run out of running replicas affecting ongoing traffic.

One suggested fix for this is to move to `exec` based healthchecks instead of `httpGet` allowing the Kubelet to not having to setup the context to send and then subsequently receive response over HTTP. But rather just executing a command in the container namespace.

# Conclusion

It was quite a ride from seeing certain requests getting timed-out to understanding how CPU limits are enforced by the Kernel. Kubernetes, as developer-friendly as it is, also comes with a lot of rough edges and it's very easy to get hit if you're not careful.


<br>

## References

- [https://medium.com/omio-engineering/cpu-limits-and-aggressive-throttling-in-kubernetes-c5b20bd8a718](https://medium.com/omio-engineering/cpu-limits-and-aggressive-throttling-in-kubernetes-c5b20bd8a718)
- [https://github.com/kubernetes/kubernetes/issues/51135](https://github.com/kubernetes/kubernetes/issues/51135)
- [https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)


