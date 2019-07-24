---
layout: post
title: Why you should learn a little Make
---

`make` is a simple utility which detects which part of a large project needs to be recompiled and executes user-defined commands to carry out compilation or other required actions. Think of a large C program which has a bunch of files. Now, you made changes to a single file and but you don't want to compile all the other files in your tree. `make` helps avoid this and recompile only the edited parts of the code. `make` was written by Richard Stallman and Roland McGrath. 

# Makefile

For `make` to work, there has to be a `Makefile` in the top level of the project. A Makefile typically has the following structure:

```
target: prerequisite
    recipe
```

- _target_ is generally a file but often times you would want to use a generalized action name as a target, we'll talk about such targets in a while.

- _prerequisite_ is a file or another target which acts as a dependency for the current target. A target can have multiple prerequisites. It is optional to have prerequisites.

- _recipe_ is an action that make carries out when the target file has been modified and/or either of the prerequisites have been. It can be a single command or a collection of commands. These are usually shell commands but there's also special syntax provided by make which you can use.

`make` has a lot of features and your Makefile can get rather complex over time with lots of new syntax. What you have above is how targets are defined in a Makefile and it will remain more or less the same everywhere.

# First target
Suppose you are working on a very trivial C program which has a source file and a header file, and your `Makefile` consists of the following:

```
main.c: header.h
    gcc main.c -o main
```

Now when you run the following command:

```
make
```

`make` will automatically determine whether the file `main.c` or any of it's prerequisites, `header.h` has changed or not and if they have, it will carry out the recipe specified and build an executable `main`. If neither of the files have not changed, on the other hand, `make` won't do anything.

- targets and phony targets
- variables and environment variables
- preprocessors
- conditional statements
- recursive make targets
- printing and not printing the commands
- creating a help target for your Makefile

- references and resources at the end
