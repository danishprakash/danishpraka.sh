---
layout: post
date: 2022-02-20
title: Kubernetes and CPU Limits
Date: 20th February 2022
---

I recently came across a rather interesting issue concerning resource limits and how they are implemented in Kubernetes. In this blogpost, I've tried to explain the problem, the cause of the problem and potential solutions to the same.

## The problem
A few requests on one of our workloads were timing out one fine day. Out of the blue, nothing out of the ordinary. Now, these timeouts would span over a few minutes and during that time, we'd also see quite a few of the pods failing their readiness and liveness probes. This happened twice in a period of ~1 month. The kind of workloads we were running, timeouts on certain requests at random wasn't acceptable at all. So we had to figure out why this was the case, even though it was just for 2 minutes that one time.

It quickly became a priority and I went about trying to figure out what really went wrong. Before going into the post, a quick disclaimer that I'm going to deliberately avoid talking about Resource Requests in this post since they are in no real way involved in the aforementioned issue. You can read more about Resources in Kubernetes [here](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/).

## Resources limits

A quick short primer. Kubernetes allows you to specify Memory and CPU limits for your workloads. There's a lot of configuration options available when it comes to managing Resources for your workloads on Kuberenetes, for e.g. QoS, LimitRanges etc. We're going to specifically focus on `spec.resources` attribute that you set in your pod manifest. The `spec.resources.request` property allows you to specify how much memory and CPU your pod would require. This information is used by the scheduler to schedule pods. But your application can certainly exceed their allocated/requested quota of resources and you don't want other workloads running on the same node to be affected by a badly behaving workload. To avoid running into this situation, you can specify `spec.resources.limits` which "ensures" your workloads never goes haywire when it comes to resource utilization.

```
...

resources:
  limits:
    cpu: 100m
    memory: 256Mi
  limits:
    cpu: 200m
    memory: 512Mi

...
```

In the above snippet, the scheduler will find nodes which have 256Mi of free memory and 100m of CPU available. Once scheduled, the pods can use more than 256Mi of memory and 100m of CPU but not beyond 512Mi and 200m.

### Memory limits

Memory being an incompressible resource, if your workloads are using more than the allocated memory limit, it will get killed. This specific event of killing a process because it is consuming more memory than it's allowed is known as OOMKilled(Out of memory killed). If and when this happens, you should be able to figure out whether you're actually experiencing an OOMKill event by going through the logs, the kernel or the container runtime dumps such events. With that, it becomes easy for you to gauge memory usage for your workloads and to decide whether you need to increase the allocated memory. Do note that in Kubernetes, an OOMKill will [not restart](https://github.com/kubernetes/kubernetes/issues/50632) your container if it's not the init container.

### CPU limits

CPU Limits work in an entirely different way. Being a compressible resource, the system based on certain heuristics, will allow or disallow CPU cycles to your process if and when your process starts to consume more than its fair share of allocated CPU. This disallowing of CPU to a process is known as throttling.

That's all well and good but when it comes to visibility, unlike memory where you can clearly find OOMKill events, figuring out whether there's any CPU throttling that your apps are experiencing is not trivial by any means. It's not impossible either, the Kernel exposes throttling metrics but it's not commonly supported by monitoring solutions and you've to set those up manually.

### How CPU Limits are enforced

The Kernel uses [CFS(Completely Fair Scheduler)](https://www.kernel.org/doc/Documentation/scheduler/sched-design-CFS.txt) to facilitate CPU allocation/disallocation to processes in a system. The CFS in turn uses two configuration options:

1. `cpu_period_us`: The CPU cycle interval which the schedueler uses to reset the used quota for a process. It's default value is 100ms.
2. `cpu_quota_us`: The total runtime for which the process can use the CPU in a given period before being reset.

Now, let's understand how this works. First of all, when you specify 1CPU as a limit for your workload, it means that the processes can use 1000 milicore/milicpu of CPU. In CFSSpeak, that means the `cpu_quota_us` would be set to 1000m. `cpu_period_us` on the other hand, is unchanged and is set to a default value of 100ms. Putting this all together, you can calculate when a process is eligible for throttling by:

```
cpu_quota_us/cpu_period_us * 1000 => x mili CPU
```

That is, once it uses x milicpu in the given `cpu_period_us`, the process will be throttled and will have its quota reset at the start of the next period.

Let's try to understand this better with the following scenarios:

- You want your process to be able to use 1 CPU completely. If it goes beyond 1CPU, it'll be, well, throttled.

```
cpu_quota_us=250ms
cpu_period_us=250ms

250/250 * 1000 => 1000m => 1CPU
```


- You want your process to be able to use 20% of a CPU:

```
cpu_quota_us=10ms
cpu_period_us=50ms

10/50 * 1000 => 200m => 0.2CPU
```

Okay, that sounds exactly like how it should behave but there's a catch, if you're running your applications in a multi-threaded environment or your pod or container (cgroup) is running multiple threads in and of itself, the `cpu_quota_us` is calculated across all the threads. Which is to say, if you're running 10 threads and you've the following config..

```
running 10 threads

cpu_quota_us=10ms
cpu_period_us=50ms

(10)/50 * 1000 => 200m CPU => 200

quota per threads = 10/10 => 1ms
```

..you'll exceed your quota in 2ms and your processes will be throttled for the remaining 48ms of that cycle. As mentioned, this is especially pronounced in multi-threaded environment and Kubernetes is a prime example. In fact, Kubernetes is the reason this issue came to light in the first place.

To state more bluntly, In the last example, when all the threads use up the allocated quota of 10ms within a period, the scheduler will not allow the process to run until the next period. This is throttling in a nutshell.

To add insult to injury, there happen\[s\|ed\] to be a [bug](https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=de53fd7aedb100f03e5d2231cfce0e4993282425) in various Linux kernel versions which aggravates this issue by throttling CPU for processes which are not close to their quota. This, again, is pronounced in multi-threaded environments like Kubernetes. Refer to [this gist](https://gist.github.com/bobrik/2030ff040fad360327a5fab7a09c4ff1) for a breakdown of what's going on.



## Solutions?
A lot of folks have experienced this issue especially when working at scale. But there was no single one-shot fix for this since there were multiple things going on. There was the obvious using up of quota within a period by multiple threads. Then there's the Kernel bug which made matters worse. That being said, you've the following options:

1. Disable CPU Limits. If there are no CPU limits on your workloads, the CFS will not come into action and the whole chaos will be averted. This has its own issues in that it's not feasible for folks to run their applications without a CPU limit. This comes down to the kind of workloads you're running i.e. optimized applications that you've written yourselves or running 3rd party binaries which you don't have any control over whatsoever when it comes to their resource usage.
2. Disabling CFS. This essentially is disabling CPU limits but you've to go through a [different route](https://github.com/kubernetes/kubernetes/pull/63437/files) to do this. And it might be possible that your cloud provided doesn't have support for this yet.
3. Reducing the `cpu_period_us` to a lower value. The default value is 100ms which a little too high when it comes to high performance web services or other such applications. Because when the cycle is longer, the processes are throttled for longer before their quota is reset. This again comes down to the kind of workloads you're deploying and it may or may not be suitable for all. For e.g. [Monzo](https://github.com/monzo/kubernetes/commit/9888ef89f3ae85e643f4d1098f0ba001414a5f25) added support for this in their own fork of Kubernetes and have [seen good results](https://github.com/kubernetes/kubernetes/issues/51135#issuecomment-384908627).
4. Update Linux kernel. This is reserved for last for a good reason. If you're reading this, there's a high probability that you're using Kubernetes as part of a cloud offering for e.g. GKE, AKS or EKS, etc. If that's the case, it becomes extremely tedious to update the Linux kernel version on your worker node images. Even if you manage to do this, it fixes part of the problem, CPU throttling would still be there as long as you have limits.

I personally tried removing the CPU limits and it worked as expected. For others, maybe disabling the CFS is easier or just waiting out for GKE et.al to come up with node images with the updated Kernel version.

## Kubelet

But wait, there's more. Remember I mentioned in passing that the pods also faced a lot of readiness and liveness probes failing? Well, I reached out to GCP for info on that.

My hypothesis was that during such a crisis i.e. the processes getting throttled and adding to that, the CFS bug in the kernel lead to the Kubelet also being in a resource crunch and hence unable to complete probes. The kubelet being unable to performa a network request to check the container health lead to a somewhat domino effect in the cluster. Pods failing the readiness and liveness probes would trigger new pods to come up unnecessarily. At the same time, some workloads already running at max would just run out of running replicas affecting ongoing traffic.

One suggested fix for this is to move to `exec` based healthchecks instead of `httpGet` allowing the Kubelet to not having to setup the context to send and then subsequently receive response over HTTP. But rather just executing a command in the container namespace.

## Conclusion
It was quite a ride from seeing certain requests getting timed-out to understanding how CPU limits are enforced by the Kernel. Kubernetes, as developer-friendly as it is, also comes with a lot of rough edges and it's very easy to get hit if you're not careful.

## References

- [https://medium.com/omio-engineering/cpu-limits-and-aggressive-throttling-in-kubernetes-c5b20bd8a718](https://medium.com/omio-engineering/cpu-limits-and-aggressive-throttling-in-kubernetes-c5b20bd8a718)
- [https://github.com/kubernetes/kubernetes/issues/51135](https://github.com/kubernetes/kubernetes/issues/51135)
- [https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)

If you found an error or an improvement in the post above, please feel free to [report it](https://github.com/danishprakash/danishpraka.sh/issues?q=is%3Aissue+is%3Aopen+sort%3Aupdated-desc).

<br>
:wq
