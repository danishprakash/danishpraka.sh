---
layout: post
date: 2022-03-20
title: Kubernetes, Deployments and failing CDs
---

## Background
There are certain deployments which, upon deploying for the first time, pull resources externally and may take a considerable amount of time before they are up and running or before they start responding successfully to probes(If you have them setup, you should if you haven't). For instance, in one of the workloads that I was working with, if any changes were made to a configMap that was fed into that pod, the pod(s) would take anywhere from 15 minutes to 1 hour to pull the relevant artifacts before showing up as [`Running`](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-phase).

Now ideally, that shouldn't be a problem but as part of our CD pipeline, we also check the deployment status of all our deployments to ensure all of them were rolled out without any issues before we trigger a subsequent pipeline. So, we essentially list all the deployments and then run the `kubectl rollout status ...` command on all of them in a sequential manner.  It looks something like this:

```
DEPLOYMENTS=$(${KUBECTL} get deploy -o custom-columns=NAME:.metadata.name --no-headers=true)
for DEPLOYMENT in ${DEPLOYMENTS[@]}; do
    ${KUBECTL} rollout status deployment $DEPLOYMENT
    if [ "$?" -ne "0" ]; then
        echo "Rollout failed for deployment: ${DEPLOYMENT}, quitting."
        exit 1
    fi
done
```

If you're wondering, yes, we can possibly also run all of them in the background using Unix job management.

## Problem
Coming back to that special configMap change which leads to certain deployments taking a lot of time than usual. By default, Kubernetes waits for a deployment to come up and the pods to be in Running state for 10minutes. After 10 minutes, Kubernetes considers this deployment a failure. This is know as `progressDeadlineSeconds`. In other words, `kubectl rollout status <deployment` command returns a non-zero exit code. It's default value, as mentioned, is 600s (==10m).

So in our case, whenever we make changes to this configMap, we basically end up having a successful deployment albeit a slow one to come up and a failed Jenkins job with failed follow-up triggers.


## Solution
You can use the `progressDeadlineSeconds` in the pod spec to a value which aligns more with the kind of workloads you are running. In our case, it can be set to 3600s. This will ensure that Kubernetes will wait for an hour for the pods for your deployment to come up before deeming it as a failure. A sample deployment.yaml manifest would then look like:

```
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
      progressDeadlineSeconds: 3600
      containers:
      - name: nginx
        image: nginx:1.14.2
        ports:
        - containerPort: 80
```

But that's not all, if you have a setup which is anything like our i.e. if you are using the `kubectl rollout status ...` command, you additionally need to specify a `--timeout=1h` flag so that the kubectl client doesn't pre-emptively return a timed out request and fail your pipeline yet again. The bash snippet shared earlier should now look like:

```
DEPLOYMENTS=$(${KUBECTL} get deploy -o custom-columns=NAME:.metadata.name --no-headers=true)
for DEPLOYMENT in ${DEPLOYMENTS[@]}; do
    ${KUBECTL} rollout status deployment $DEPLOYMENT --timeout=1h
    if [ "$?" -ne "0" ]; then
        echo "Rollout failed for deployment: ${DEPLOYMENT}, quitting."
        exit 1
    fi
done
```

## Conclusion
This was supposed to be a short post and I'd reiterate again the use case depicted above is very specific but it's interesting how Kubernetes caters to a wide array of use-cases and how there are, at least now, a myriad of Kubernetes features that haven't gained mainstream adoption yet which I think is understandable.

## References
- [https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#progress-deadline-seconds](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#progress-deadline-seconds)

If you found an error or an improvement in the post above, please feel free to [report it](https://github.com/danishprakash/danishpraka.sh/issues?q=is%3Aissue+is%3Aopen+sort%3Aupdated-desc).

<br>
:wq

