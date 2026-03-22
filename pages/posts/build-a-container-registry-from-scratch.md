---
layout: post
date: 2026-03-22
title: Build a Container Registry from Scratch
tags: containers, programming
---

In a previous [article](/posts/build-a-container-image-from-scratch/), we built a container image from scratch to understand the OCI image format. In this article, we will explore how container registries work by building a minimal one from scratch.

Being able to distribute containers efficiently, securely, and at scale is one of the primary reasons why containers are so ubiquitous. There are countless registries available online that store and distribute pre-built and custom container images. Docker Hub and Quay.io are a few of the popular ones. Registries allow us to distribute our container images to other users, and at the same time, allow us to use container images authored and built by others, reducing the usual overhead that comes with writing [Containerfiles](/posts/dockerfile-practices).

This article tries to answer the following question—"What happens when you do `podman push/pull`?" We'll do so by creating a simple container registry--we'll call it tiny-registry—using pure Go under 200 lines that will respond to push and pull commands from any container engine (we'll be using podman for our use case).

## What makes a registry?

### OCI Distribution Spec
The OCI Image Spec defines the structure of a container image, while the OCI Distribution Spec defines how clients interact with a registry.

In simpler terms, the OCI Distribution Spec defines a set of API endpoints that a registry needs to handle for it to be considered compliant with the OCI Distribution Spec _and_ act as a functional container registry that clients can interact with.

Conformance with the spec is defined for various categories, but at the bare minimum, a registry should support all the API endpoints that correspond to an image PULL. Our tiny-registry will support a few more endpoints than just PULL to support `podman pull` and `podman push` against our registry. The list of endpoints we will support is as follows:

```
GET     /v2/ — version check (clients probe this first)
GET     /v2/{name}/manifests/{reference} — pull manifest (handles both tags and digest refs)
GET     /v2/{name}/blobs/{digest} — pull blob
POST    /v2/{name}/blobs/uploads/ — initiate upload session
PATCH   /v2/{name}/blobs/uploads/{session} — stream blob data
PUT     /v2/{name}/blobs/uploads/{session} — finalize blob (rename tmp → blobs/)
PUT     /v2/{name}/manifests/{reference} — store manifest
```

Let's get to the implementation. Since this is a demo registry, our goal is to ensure our registry can support push and pull from container engines. This means we should be able to `podman push` a container image to our registry, and subsequently `podman pull` that same image and be able to run a container off of it.

## 1. Push — _to the registry_

### 1.1 Storage model: _storing the image_

If you [recall](/posts/build-a-container-image-from-scratch/), an OCI image consists of 4 key components, the image index, an image manifest, the image config, and the layer blobs. All of these are content addressable objects, except for the image index in an OCI layout. The registry doesn't have to deal with `index.json` although it _can_ store them for multi-arch images. All it needs to do really, as we saw before, is to handle the routes as stated in the OCI Distribution Spec.

This means we're concerned with storing only the manifest and the blobs on the host filesystem. The distribution spec doesn't mention anything about _how_ you store these components on the filesystem, it's only concerned with how you serve them to the client—by following the API endpoints it defines.

For the tiny-registry, we can simplify things by having the following directory structure:

```
registry/
├── blobs/
│   ├── sha256:216659b5...   ← manifest (also stored as blob)
│   ├── sha256:a3b655d4...   ← layer blob
│   └── sha256:af3f0f48...   ← config blob
├── {name}/
│   └── manifests/
│       └── latest           ← pointer file, contains the manifest digest
│       └── v1               ← pointer file, contains the manifest digest
└── tmp/                     ← staging area for in-progress uploads
```

- `blobs/` - Leveraging the benefits of content-addressability, we have one single directory where we'll store all the blobs of all the images ie the layers, manifests, and configs.
    - This helps us avoid duplication since if there are two images sharing layers, we'll only store one copy of it on the filesystem and serve that file when a pull request comes in for either of those images.
- `{name}/` - We create a new directory for every image that would store the manifests' sha256 digest. This corresponds to an image tag, and for every additional tag for this image, we'll create a new file.
- `tmp/` - This is a temporary directory used as part of the PUSH flow; we'll use this for rudimentary session handling our tiny-registry will implement.

Production-grade registries typically use object storage (such as S3) instead of a local filesystem, and maintain metadata in a database. The underlying idea, however, remains the same.

### 1.2 Upload protocol: _the push endpoints_
Now let's understand the API endpoints corresponding to the PUSH workflow. A client can push a blob in two ways, either chunked or monolithically. Podman typically performs chunked uploads. It has obvious advantages over monolithic especially when it comes to pushing large blobs, most important being not having to start the push from scratch if your connection to the registry was interrupted for some reason.

For our registry to support chunked push, we have to support the following routes:

```
GET     /v2/                                    handleVersion

POST    /v2/{name}/blobs/uploads/               handleInitUpload
PATCH   /v2/{name}/blobs/uploads/{session}      handlePatchBlob
PUT     /v2/{name}/blobs/uploads/{session}      handleFinalizeBlob
PUT     /v2/{name}/manifests/{reference}        handlePutManifest
```

A chunked push has essentially 4 parts to it that are handled by 4 different HTTP handlers in our code:

0. `handleVersion` - This is to confirm whether the registry is Distribution Spec compliant. We return 200, and the client continues. The client runs this everytime it attempts to engage with the registry as part of a workflow, push or pull for instance.
1. `handleInitUpload` - This initializes the upload by creating an empty file under `./registry/tmp/<sessionID>` where sessionID is a random 16-digit hex code.
2. `handlePatchBlob` - The client streams the blob data, we append it to tmp/<sessionID>, and return `202 Accepted`.
3. `handleFinalizeBlob` - Client says "I'm done sending the blob, here's the expected digest". We rename `registry/tmp/<sessionID>` to `blobs/sha256:...`, and return 201.
4. `handlePutManifest` - Once all the blobs are uploaded, client sends the manifest JSON for the image as the body. We compute the digest of the manifest, store it under blobs, and write that digest under `{name}/manifests/{tag}`.

### 1.3 Implementation
Here's what our Go pseudocode looks like when it's handling the PUSH workflow:

```
// routes
mux.HandleFunc("GET /v2/", handleVersion)
mux.HandleFunc("POST /v2/{name}/blobs/uploads/", handleInitUpload)
mux.HandleFunc("PATCH /v2/{name}/blobs/uploads/{session}", handlePatchBlob)
mux.HandleFunc("PUT /v2/{name}/blobs/uploads/{session}", handleFinalizeBlob)
mux.HandleFunc("PUT /v2/{name}/manifests/{reference}", handlePutManifest)

func handleInitUpload(w http.ResponseWriter, r *http.Request) {
    rand.Read(b)
    sessionID := hex.EncodeToString(b)
    os.Create("registry/tmp/" + sessionID)
    w.Header().Set("Location", "/v2/"+name+"/blobs/uploads/"+sessionID)
}

func handlePatchBlob(w http.ResponseWriter, r *http.Request) {
    data, _ := io.ReadAll(r.Body)
    f, _ := os.OpenFile("registry/tmp/"+sessionID, os.O_APPEND|os.O_WRONLY, 0o644)
    f.Write(data)
}

func handleFinalizeBlob(w http.ResponseWriter, r *http.Request) {
    digest := r.URL.Query().Get("digest")
    os.Rename("registry/tmp/"+sessionID, "registry/blobs/"+digest)
}

func handlePutManifest(w http.ResponseWriter, r *http.Request) {
    digest := fmt.Sprintf("sha256:%x", sha256.Sum256(data))
    os.WriteFile("registry/blobs/"+digest, data, 0o644)
    os.WriteFile("registry/"+name+"/manifests/"+reference, []byte(digest), 0o644)
}
```

The above should be considered pseudocode as I've tried to simplify by only showing the routes and the happy paths. It would be wasteful to paste the complete source here. You can always take a look at the source code [here](https://github.com/danishprakash/tiny-registry).

The methods and handlers we defined above would allow our registry to respond to a client's push request, a `podman push` for instance, and store the image blobs and manifest on the host filesystem. We'll bring it all together in a later section and see how it all works.

## 2. Pull — _from the registry_

Since we already defined the filesystem layout, implementing support for the PULL workflow is simpler in comparison. For starters, we need to support the following API endpoints:

```
GET /v2/                                 handleVersion

GET /v2/{name}/manifests/{reference}     handleGetManifest
GET /v2/{name}/blobs/{digest}            handleGetBlob
```

1. `handleGetManifest` - When pulling, the client first requests the manifest, and uses it to further request the blobs by digest.
    - If you recall, we store the manifest by its content-addressable name under blobs/ and store that digest under `./registry/{name}/manifests/{tag}`
    - So we first read the digest and then return the actual contents from `./registry/blobs/sha256...`.
2. `handleGetBlob` - Once the client has the manifest, it will request the config and layer blobs by referring to their digests.

Here's what the Pull implementation looks like:

```
// routes
mux.HandleFunc("GET /v2/", handleVersion)
mux.HandleFunc("GET /v2/{name}/manifests/{reference}", handleGetManifest)
mux.HandleFunc("GET /v2/{name}/blobs/{digest}", handleGetBlob)

func handleGetManifest(w http.ResponseWriter, r *http.Request) {
    digest, _ := os.ReadFile("registry/" + name + "/manifests/" + reference)
    data, _ := os.ReadFile("registry/blobs/" + string(digest))
    w.Write(data)
}

func handleGetBlob(w http.ResponseWriter, r *http.Request) {
    data, _ := os.ReadFile("registry/blobs/" + digest)
    w.Write(data)
}
```

## 3. Execution — _tracing a push/pull_

### 3.1 Tracing an image push
Once we're done with the implementation, let's run our registry and test it:

```
$ tree tiny-registry
.
├── go.mod
└── main.go
```

Looking at our tiny-registry source directory, we can see it doesn't have a lot going on: a go.mod file, and our main.go file that houses all the logic we've discussed so far. Let's now try to push an image to our registry:

```
$ go run main.go &

$ podman push --tls-verify=false busybox:latest localhost:8080/busybox:latest
GET     /v2/

HEAD    /v2/busybox/blobs/sha256:a3b655d4356d3eafbfce127e94844901a68074eb6fde905780d46cabf0caf342
ERROR   getting blob: open registry/blobs/sha256:a3b655d4356d3eafbfce127e94844901a68074eb6fde905780d46cabf0caf342: no such file or directory

POST    /v2/busybox/blobs/uploads/
PATCH   /v2/busybox/blobs/uploads/82d84bdff2813060a23991fde157fcf5 name=busybox sessionID=82d84bdff2813060a23991fde157fcf5
PUT     /v2/busybox/blobs/uploads/82d84bdff2813060a23991fde157fcf5 name=busybox sessionID=82d84bdff2813060a23991fde157fcf5

HEAD    /v2/busybox/blobs/sha256:af3f0f48a24edb84e94aff6f44f5d089203453719d3b2328486d311e61db9b09
ERROR   getting blob: open registry/blobs/sha256:af3f0f48a24edb84e94aff6f44f5d089203453719d3b2328486d311e61db9b09: no such file or directory

POST    /v2/busybox/blobs/uploads/
PATCH   /v2/busybox/blobs/uploads/d659ef9bb0583136ec814301a63d1eae name=busybox sessionID=d659ef9bb0583136ec814301a63d1eae
PUT     /v2/busybox/blobs/uploads/d659ef9bb0583136ec814301a63d1eae name=busybox sessionID=d659ef9bb0583136ec814301a63d1eae

PUT     /v2/busybox/manifests/latest name=busybox reference=latest
```

You can note the order of execution from the registry's viewpoint.

- `GET`: Client does the API version check first.
- `HEAD`: Client checks if the layer blob exists or not.
- `ERROR`: It doesn't; so the client initiates the upload.
- `POST-PATCH-PUT`: The client streams the blob to the registry.
- `POST-PATCH-PUT`: The client repeats the same for the config blob.
- `PUT`: Finally, the client uploads the manifest, marking the end of the flow.

### 3.2 Tracing an image pull
Similarly, let's take a look at the pull flow:

```
$ podman pull --tls-verify=false localhost:8080/busybox:latest
GET     /v2/
GET     /v2/busybox/manifests/latest name=busybox reference=latest
GET     /v2/busybox/blobs/sha256:af3f0f48a24edb84e94aff6f44f5d089203453719d3b2328486d311e61db9b09 digest=sha256:af3f0f48a24edb84e94aff6f44f5d089203453719d3b2328486d311e61db9b09
GET     /v2/busybox/blobs/sha256:a3b655d4356d3eafbfce127e94844901a68074eb6fde905780d46cabf0caf342 digest=sha256:a3b655d4356d3eafbfce127e94844901a68074eb6fde905780d46cabf0caf342
```

This is relatively straightforward. Client does a version check, followed by pulling the manifest, and from the manifest, it pulls the config and the layer blob; marking the pull complete.

The sequence above mirrors the upload and download flow we described earlier, but now shows actual requests and responses between a client and a registry. Lastly, as a sanity check, we can test if the image we pushed to our registry and pulled from it, works as expected:

```
$ podman run --rm localhost:8080/busybox:latest echo "it works"
it works
```

There we have it, our tiny-registry responds to the `podman` `push` and `pull` commands, successfully storing an image that was pushed, and then serving it back to the client.

Since podman by default refuses to talk to registries over plain HTTP, `--tls-verify=false` allows us to play around with our registry on localhost without the overhead of provisioning a deployment or TLS cert.

### 3.3 Inspecting our local storage
Lastly, let's take a look at how our `registry/` directory on our filesystem looks like after the above interactions with the registry:

```
$ tree ./registry
.
├── blobs
│   ├── sha256:216659b5706c007bcf2bcec124a6d32ad2ecbfd9b1921c695e022b7a4a27a0d9
│   ├── sha256:a3b655d4356d3eafbfce127e94844901a68074eb6fde905780d46cabf0caf342
│   └── sha256:af3f0f48a24edb84e94aff6f44f5d089203453719d3b2328486d311e61db9b09
├── busybox
│   └── manifests
│       └── latest
└── tmp

$ cat ./registry/busybox/manifests/latest
sha256:216659b5706c007bcf2bcec124a6d32ad2ecbfd9b1921c695e022b7a4a27a0d9
```

As we discussed earlier, the manifest, the layer, and the config.json for the busybox image we had pushed are stored under `blobs/`, with tags pointing to the corresponding manifest digests.

At a high-level, a registry is a thin HTTP wrapper over a content-addressable storage. Adding features or making it robust makes the registry more appealing but the idea remains fundamentally the same.

## Limitations

As the name suggests, this is a demo registry. So, while the Distribution Spec defines additional workflows such as Content Discovery and Content Management, we've implemented only the Push and Pull workflows. Even in those workflows, we've implemented basic functionality for the sake of demonstration and skipped features such as multi-arch support, authentication, content-type validation, etc.

Projects such as [distribution](https://github.com/distribution/distribution) implement the full OCI Distribution specification, and act as a full-fledged registry solution.

## Conclusion

We built a minimal registry that implements just enough of the OCI Distribution specification to support `push` and `pull` commands from any container engine. In doing so, we saw how a registry stores image data—manifests, configs, and layer blobs, and how it serves them via a small set of HTTP endpoints.

The next time you run `podman push` or `pull`, you can mentally map the requests to API endpoints and the content-addressed blobs being transmitted and stored by the registry.


:wq
