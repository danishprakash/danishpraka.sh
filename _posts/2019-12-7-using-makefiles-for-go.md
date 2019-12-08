---
layout: post
title: Using Makefile(s) for Go
---

We've been using `make` as a build tool for one of our project at HackerRank which is written in Go and it has been working out fairly well. In this post, I'll point out a few features and intricacies of GNU Make we've used which eventually improved the overall productivity of members in our team.

# Introduction
`make` is a simple utility which detects which part of a large project needs to be recompiled and executes user-defined commands to carry out compilation or other required actions. It's also widely used a build tool wherein you specify a set of commands to be run which you inherently used to write on the command-line repeatedly. The latter is what the rest of this post is about.

For the purpose of this post, we'll assume we are working on a Go project, `stringifier` and will be writing a Makefile for the same which is also named `Makefile`.

# Build and Run
These are two actions that go programmers use pretty frequently, so let's add these targets to our Makefile:

```make
build:
	go build -o stringifier main.go

run:
	go run -race main.go
```
I added the `-race` flag to the run command because it detects race conditions in your go code when you run it which is an otherwise unpleasent exercise.

# Cleaning and DRYing
After building the binary and running the application just fine, let's make sure we are cleaning the binaries before proceeding with anything else. Our updated Makefile should look something like this:

```make
build:
	go build -o stringifier main.go

run:
	go run -race main.go

clean:
	rm -rf stringifier
```
There are two things we can improve upon here, first, we are explicitly reusing our application name, it's natural that our application name will be used in a myriad of places throughout our Makefile, we should reuse that. Second, we need to run the `clean` rule before we go ahead and `build` our application every time, let's fix these:

```make
APP=stringifier


build: clean
	go build -o ${APP} main.go

run:
	go run -race main.go

clean:
	rm -rf ${APP}
```
Looks much cleaner, doesn't it? You can define Makefile variables at the top and make will automatically expands them when you invoke the `make` command.

# PHONY targets
By design, make executes the rule if one of the prerequisites or the target file has been changed. But since we are are not relying on the ability of make to detect file changes, we are putting ourselves in a potential pit. 

Imagine that there's a file in our project directory named `build`, again this is a hypothetical situation. In this case, when you run `make build`, make will check for changes to the file `build` and it's prerequisites which there are none and hence won't execute the recipe which is not what we want. We might end up using the existing binary for our use, which is misleading and a road to a lot of confusion down the road.

To avoid this problem, you can specify the target in question to be "phony" by specifying it as a prerequisite to the special target `.PHONY`:

```make
APP=stringifier


.PHONY: build
build: clean
	go build -o ${APP} main.go

.PHONY: run
run:
	go run -race main.go

.PHONY: clean
clean:
	rm -rf ${APP}
```

Now that you've specified all the above targets as phony, make will run the recipes inside of the rules every time you invoke any of the phony targets. You can also specify all the targets you want to specify as phony at once like so:

```make
.PHONY: build clean run
```

But for Makefiles which grow really big, this is not suggested as it could lead to ambiguity and unreadability, hence the preferred way is to explicitly set phony target right before the rule definition.

# Recursive Make targets
Let us now assume that we have another module `tokenizer` in our root directory that we use in our project. Our directory structure is now something like this:

```text
~/programming/stringifier
.
├── main.go
├── Makefile
└── tokenizer/
      ├── main.go
      └── Makefile
```

Quite naturally, at some point, we would like to build and test our `tokenizer` module as well. Since it's a separate module and a potentially separate project at some point, it makes sense for it to have a Makefile in it's directory (cue for the post title) with the following content:

```make
# ~/programming/stringifier/tokenizer/Makefile

APP=tokenizer

build:
	go build -o ${APP} main.go
```

Now, anytime you are in the root directory of your `stringifier` project and want to build the tokenizer application, you wouldn't want to give in to hacky command-line tricks such as `cd tokenizer && make build && cd -` to invoke rules in Makefiles written in sub-directories. Thankfully, make can help you with that, you can invoke make targets in other directories using the `-C` flag and the special `${MAKE}` variable. This is the original Makefile from the `stringifier` project:

```make
# ~/programming/stringifier/Makefile

APP=stringifier


.PHONY: build
build: clean
	go build -o ${APP} main.go

.PHONY: run
run:
	go run -race main.go

.PHONY: clean
clean:
	rm -rf ${APP}

.PHONY: build-tokenizer
build-tokenizer:
	${MAKE} -C tokenizer build
```

Now, anytime you run `make build-tokenizer`, make will handle the directory switching for you and will invoke the right target in the right directory for you in a much more readable and robust manner.

# Targets for Docker commands
Now you wish to [containerize](https://www.ibm.com/cloud/learn/containerization#toc-what-is-co-r25Smlqq) your application and susequently write make targets for the same for convenience which is completely understandable.

Now, you have the following rules defined for the docker commands:

```make
.PHONY: docker-build
docker-push: build
	docker build -t stringifier .
	docker tag stringifier stringifier:tag

.PHONY: docker-push
docker-push: docker-build
	docker push gcr.io/stringifier/stringifier-staging/stringifier:tag
```

Ok but now there's room for improvement yet again, for starters, you can reuse your `${APP}` variable again. Next, you need to be rather flexible and make sure you can easily control where you push your image, whether that's your private registry or some place else. Then, you would like to be able to push your image to two separate registries pertaining to staging and production environments respectively based on some input on the command-line from the user. Finally, like a sane developer, you would like to tag your images, with the current git commit sha, in your case. Let's fix things up:

```make
APP?=application
REGISTRY?=gcr.io/images
COMMIT_SHA=$(shell git rev-parse --short HEAD)

.PHONY: docker-build
docker-push: build
	docker build -t ${APP} .
	docker tag ${APP} ${APP}:${COMMIT_SHA}

.PHONY: docker-push
docker-push: check-environment docker-build
	docker push ${REGISTRY}/${ENV}/${APP}:${COMMIT_SHA}

check-environment:
ifndef ENV
    $(error ENV not set, allowed values - `staging` or `production`)
endif
```
Okay now, let's go over the changes above:

- You started using variables for the application name, the image registry and for the commit sha.
- You generated the commit sha using the special `shell` function. In this case, you ran the `git` command which returned the short commit sha and assigned it to the variable `${COMMIT_SHA}` to be used later on in your Makefile.
- You added a new rule `check-environment` which uses the make conditionals to check whether the `ENV` variable is specified or not while invoking make. This helps removing the ambiguity to which repo, out of staging and environment, to push the the docker image of your application.

Expanding on the `check-environment` rule here:

```make
check-environment:
ifndef ENV
    $(error ENV not set, allowed values - `staging` or `production`)
endif
```

You are using the `ifndef` directive which checks whether the variable `ENV` has an empty value or not, and if it does, then you use another built-in function that make provides, `error` which, as it sounds, throws an error with the error message following the keyword.

```shell
$ make docker-push
Makefile:33: *** ENV not set, allowed values - `staging` or `production`.  Stop.

$ ENV=staging make docker-push
Success
```

Essentially, you are making sure that the `docker-push` target has a safety net which checks that the user who invoked the target has specified a value for the `ENV` variable.

# Help target
A new member has joined the project and is wondering what all the rules do in the Makefile, to help them out, you can add a new target which will print all the target names along with a short description of what they do:

```make
.PHONY: build
## build: build the application
build: clean
    @echo "Building..."
    @go build -o ${APP} main.go

.PHONY: run
## run: runs go run main.go
run:
	go run -race main.go

.PHONY: clean
## clean: cleans the binary
clean:
    @echo "Cleaning"
    @rm -rf ${APP}

.PHONY: setup
## setup: setup go modules
setup:
	@go mod init \
		&& go mod tidy \
		&& go mod vendor
	
.PHONY: help
## help: prints this help message
help:
	@echo "Usage: \n"
	@sed -n 's/^##//p' ${MAKEFILE_LIST} | column -t -s ':' |  sed -e 's/^/ /'
```

Focus on the last rule, `help`. Here, you are simply using some `sed` magic to parse and print on the command line. But to do that, you already wrote the target name and a short description before every rule as comments. Notice another special variable, `${MAKEFILE_LIST}` which is a list of all the Makefiles you have referred to, only `Makefile` in our case.

You are passing the file `Makefile` as input to the `sed` command which is parsing all the help comments and printing them to the stdout in a tabular format so that's it's easier to read. Output for the `help` target for the previous snippet would look like the following:

```shell
$ make help
Usage:
	build             Build the application
	clean             cleans the binary
	run               runs go run main.go
	docker-build      builds docker image
	docker-push       pushes the docker image
	setup             set up modules
	help              prints this help message
```

Well, that looks quite helpful. It will most certainly come in handy for a lot of people and even for you at times.

# Conclusion
Make is a simple yet a highly configurable tool. In this post, you ran through a host of configurations and features offerred by make to write an effective and productive Makefile for your go application.

Here's the complete Makefile after adding a few trivial rules and variables for completeness's sake:

```make
GO11MODULES=on
APP?=application
REGISTRY?=gcr.io/images
COMMIT_SHA=$(shell git rev-parse --short HEAD)



.PHONY: build
## build: build the application
build: clean
    @echo "Building..."
    @go build -o ${APP} main.go

.PHONY: run
## run: runs go run main.go
run:
	go run -race main.go

.PHONY: clean
## clean: cleans the binary
clean:
    @echo "Cleaning"
    @rm -rf ${APP}

.PHONY: test
## test: runs go test with default values
test:
	go test -v -count=1 -race ./...


.PHONY: build-tokenizer
## build-tokenizer: build the tokenizer application
build-tokenizer:
	${MAKE} -c tokenizer build

.PHONY: setup
## setup: setup go modules
setup:
	@go mod init \
		&& go mod tidy \
		&& go mod vendor
	
# helper rule for deployment
check-environment:
ifndef ENV
    $(error ENV not set, allowed values - `staging` or `production`)
endif

.PHONY: docker-build
## docker-build: builds the stringifier docker image to registry
docker-push: build
	docker build -t ${APP}:${COMMIT_SHA} .

.PHONY: docker-push
## docker-push: pushes the stringifier docker image to registry
docker-push: check-environment docker-build
	docker push ${REGISTRY}/${ENV}/${APP}:${COMMIT_SHA}

.PHONY: help
## help: Prints this help message
help:
	@echo "Usage: \n"
	@sed -n 's/^##//p' ${MAKEFILE_LIST} | column -t -s ':' |  sed -e 's/^/ /'
```

If you found any issues/mistakes or have any suggestions or additions related to this post, please feel free to reach out to me.

---
