---
layout: post
title: Write a shell in Python
---

One of the first post I wrote here, [Write a shell in C](https://danishprakash.github.io/2018/01/15/write-a-shell.html), described how to write a functional shell for \*nix based systems. When I was undertaking that project, I wanted to write it in Python but I ended up choosing C for the task. A recent discussion with a friend of mine lead me to write this post and since I started, it turns out that it is really easy to write a shell in Python.

We'll write a simple shell that that will support almost all the basic commands. We'll also implement piping for our shell which will allow us to pipe the output of a command as input to another command, more on that later.

# Program flow
We'll start off with our `main` function where we will handle the program flow. First, let's get the user input which is quite trivial, we'll just run an infinite loop and prompt the user for input.

```python
def main():
    while True:
        command = input("$ ")
        if command == "exit":
            break
        elif command == "help":
            print("psh: a simple shell written in Python")
        else:
            execute_commands(command)
```

We're handling the `exit` command simply by breaking out of the loop. The next most important task is to execute the command entered by the user which we'll manage in a separate function, let's call that `execute_commands(command)`. We've also added a simple `help` function to let the user know what's actually happening.

# Executing commands
Let's execute the commands entered by the user. We're using the `subprocess` builtin module here, so `import subprocess` and we're good to go. The `run` function in particular is used here to execute commands in a subshell. For those coming from C, this saves us from going about forking and creating a child process and then waiting for the child to finish execution, let Python take care of that this one time.

```python
def execute_commands(command):
    try:
        subprocess.run(command.split())
    except Exception:
        print("psh: command not found: {}".format(command))
```

We're making sure that our shell doesn't come crashing down if the user enters `cs` instead of `cd` by mistake, hence the `try/except` mechanism. Just a heads up, there are many other ways to execute system commands from within Python including `os.system` and `commands` etc but using `subprocess` is the [preferred](https://docs.python.org/2/library/commands.html) [way](https://docs.python.org/3/library/os.html?%20system#os.system) of doing it.

# Changing the directory
While all our commands would work using the `subprocess` module, the `cd` command would not work this way. This is because subprocess runs the command in a subshell and when you try to change the directory, it actually changes the directory but does so in the subshell instead of in the original process and hence we get the impression that the command didn't work. We'll handle this separately in a different function and add a conditional in our `main` function.

```python
def psh_cd(path):
    """convert to absolute path and change directory"""
    try:
        os.chdir(os.path.abspath(path))
    except Exception:
        print("cd: no such file or directory: {}".format(path))
```

Here, we're using `os.chdir` to change the directory and we also make sure to convert the path entered by the user to an absolute path before passing it to `os.chdir`. Note that we'll have to edit our main function to add this condition.

# Pipes!
Let's get to the fun part. Pipes allow us to transfer output of one process as input to another and so on, in a chained manner. Consider this image\[[1](http://web.cse.ohio-state.edu/~mamrak.1/CIS762/pipes_lab_notes.html)] which shows how pipes are used and what they do.

![img](http://web.cse.ohio-state.edu/~mamrak.1/CIS762/unix_pipes.gif)

You can think of a pipe `|` as a pair of file descriptors. For instance, If we create a pipe, we'll get two file descriptors reserved for our usage, for e.g. `f1` and `f2` wherein we can write data to `f2` and read the same from `f1`. Python allows us to create pipes using `os.pipe` which returns a tuple containing the integer value which refer to the file descriptors. Consider the implementation of our `execute_commands` function with piping below:

```python
def execute_command(command):
    """execute commands and handle piping"""
    try:
        if "|" in command:
            # save for restoring later on
            s_in, s_out = (0, 0)
            s_in = os.dup(0)
            s_out = os.dup(1)

            # first command takes commandut from stdin
            fdin = os.dup(s_in)

            # iterate over all the commands that are piped
            for cmd in command.split("|"):
                # fdin will be stdin if it's the first iteration
                # and the readable end of the pipe if not.
                os.dup2(fdin, 0)
                os.close(fdin)

                # restore stdout if this is the last command
                if cmd == command.split("|")[-1]:
                    fdout = os.dup(s_out)
                else:
                    fdin, fdout = os.pipe()

                # redirect stdout to pipe
                os.dup2(fdout, 1)
                os.close(fdout)

                try:
                    subprocess.run(cmd.strip().split())
                except Exception:
                    print("psh: command not found: {}".format(cmd.strip()))

            # restore stdout and stdin
            os.dup2(s_in, 0)
            os.dup2(s_out, 1)
            os.close(s_in)
            os.close(s_out)
        else:
            subprocess.run(command.split(" "))
    except Exception:
        print("psh: command not found: {}".format(command))
```

Here, we have created a pipe with the values `fdin` and `fdout`. We're manipulating our file descriptors using the pipe we've created, so the input and output of every sub-command(each of the piped commands) executed during the loop will depend on the value of `fdin` and `fdout`.

Don't fret if that seemed confusing, let's see what's happening in the above snippet of code line-by-line.

- __Lines 6-7:__ We're creating temporary variables, `s_in`, `s_out` to hold the original values of `stdout` and `stdin` to restore them later on.
- __Line 11:__ Create a duplicate of `stdin` and set `fdin` to it so that the first sub-command recieves input from `stdin` when we later redirect the standard input to `fdin`.
- __Line 14:__ The loop iterates over the sub-commands.
- __Line 17-18:__ Redirecting `stdin` to `fdin`. There can be two cases here. First, if the sub-command is the first in series, then `fdin` would be pointing to `stdin` . Second, if the sub-command is not the first, in which case, the value of `fdin` would be storing the value of the readable end of the pipe we have created in the previous iteration of the loop.
- __Lines 21-28:__ Redirecting `stdout` to `fdout`. There are two possibilites here as well. First, if the sub-command is the last in series, in that case, `fdout` would be redirected to `s_out`, which is the original `stdout` we stored. Second, if the sub-command is not the last in series, in which case, we would redirect `fdout` to the writable end of of the pipe we have created in this very iteration of the loop. Note that in line 24, we are creating the pipe.
- __Lines 30-33:__ We're executing the sub-command here. It will read input from `fdin` and will write it's output to `fdout` theoretically since we redirected both `stdin` and `stdout` accordingly.
- __Lines 36-39:__ We're restoring the values of `stdin` and `stdout` to their original values that we had stored earlier.
- __Lines 40:__ Execute the command normally if no pipe operators are present.

# Putting it together
We have all the pieces figured out now. Let's put them together to get this shell working. I've made some additions here and there which are too trivial to explain before putting it out here. You can also see the sample output below the code.

```python
#!/usr/bin/env python3

"""psh: a simple shell written in Python"""

import os
import subprocess


def execute_command(command):
    """execute commands and handle piping"""
    try:
        if "|" in command:
            # save for restoring later on
            s_in, s_out = (0, 0)
            s_in = os.dup(0)
            s_out = os.dup(1)

            # first command takes commandut from stdin
            fdin = os.dup(s_in)

            # iterate over all the commands that are piped
            for cmd in command.split("|"):
                # fdin will be stdin if it's the first iteration
                # and the readable end of the pipe if not.
                os.dup2(fdin, 0)
                os.close(fdin)

                # restore stdout if this is the last command
                if cmd == command.split("|")[-1]:
                    fdout = os.dup(s_out)
                else:
                    fdin, fdout = os.pipe()

                # redirect stdout to pipe
                os.dup2(fdout, 1)
                os.close(fdout)

                try:
                    subprocess.run(cmd.strip().split())
                except Exception:
                    print("psh: command not found: {}".format(cmd.strip()))

            # restore stdout and stdin
            os.dup2(s_in, 0)
            os.dup2(s_out, 1)
            os.close(s_in)
            os.close(s_out)
        else:
            subprocess.run(command.split(" "))
    except Exception:
        print("psh: command not found: {}".format(command))


def psh_cd(path):
    """convert to absolute path and change directory"""
    try:
        os.chdir(os.path.abspath(path))
    except Exception:
        print("cd: no such file or directory: {}".format(path))


def psh_help():
    print("""psh: shell implementation in Python.
          Supports all basic shell commands.""")


def main():
    while True:
        inp = input("$ ")
        if inp == "exit":
            break
        elif inp[:3] == "cd ":
            psh_cd(inp[3:])
        elif inp == "help":
            psh_help()
        else:
            execute_command(inp)


if '__main__' == __name__:
    main()
```

```shell
# running the shell
$ python3 psh.py

# prompt from our shell
$ pwd
/home/psh

# pipe multiple commands 
$ cat psh | wc -l
      81
```
<br>
--

# Conclusion
So we've written a functional shell in Python in about ~80 lines of code, that's not too bad considering we've got piping sorted out here. There are a lot of features missing from this shell but the intent behind this was not turning this into a daily driver but to rather see the implementation of a shell in Python. In the process, we learned how to execute system commands from within Python the right way, we also learned how to manipulate file descriptors in Python to redirect input/output of a command as per our needs.

For further practice, you can try implementing the following features in this shell

- Implement the `history` command, see [this](https://github.com/danishprakash/dash) for reference.
- Add [globbing](http://tldp.org/LDP/abs/html/globbingref.html) support.
- Add comment support at the prompt.Comments are disregarded by the shell so this should be fairly trivial.

If you find any issues/mistakes in this post, contact me or open an issue on this project's [repository](https://github.com/danishprakash/psh).

---
