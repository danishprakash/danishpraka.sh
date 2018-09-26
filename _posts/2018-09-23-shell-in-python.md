---
layout: post
title: Writing a shell in Python
---

One of the first posts I wrote on this blog of mine - [Write a shell in C](https://danishprakash.github.io/2018/01/15/write-a-shell.html) - described how to write a functional shell for \*nix based systems. When I was undertaking that project, I wanted to write it in Python but I ended up choosing C for the task. A recent discussion with a friend of mine lead me to write this post and since I started, it turns out that it is really easy to write a shell in Python.

We'll write a simple shell that that will support almost all the basic commands. We'll also implement piping for our shell which will allow us to pipe the output of a command as input to another command. 

# Program flow
We'll start off with our `main` function where we will handle the program flow. First, let's get the user input which is quite trivial, we'll just run an infinite loop and prompt the user for input.

{% highlight python linenos %}
def main():
    while True:
        command = input("$ ")
        if command == "exit":
            break
        elif command == "help":
            print("psh: a simple shell written in Python")
        else:
            execute_commands(command)
{% endhighlight %}

We're handling the `exit` command simply by breaking out of the loop. The next most important task is to execute the command entered by the user which we'll manage in a separate function, let's call that `execute_commands(command)`. Also, while we're at it, let's add a simple `help` function to let the user know what's actually happening.

# Executing commands
Let's execute the commands entered by the user. We're using the `subprocess` builtin module here, so `import subprocess` and we're good to go. The `run` function in particular is used here to execute commands in a subshell. For those coming from C, this saves us from going about forking and creating a child process and then waiting for the child to finish execution, let Python take care of that this one time.

{% highlight python linenos %}
def execute_commands(command):
    try:
        subprocess.run(command.split())
    except Exception:
        print("psh: command not found: {}".format(command))
{% endhighlight %}

We're making sure that our shell doesn't come crashing down if the user enters `cs` instead of `cd` by mistake, hence the `try/except` mechanism. Just a heads up, there are many other ways to execute system commands from within Python including `os.system` and `commands` etc but using `subprocess` is the [preferred](https://docs.python.org/2/library/commands.html) [way](https://docs.python.org/3/library/os.html?%20system#os.system) of doing it.

# Changing the directory
While all our commands would work using the `subprocess` module, the `cd` command would not work this way. This is because subprocess runs the command in a subshell and when you try to change the directory, it actually changes the directory but does so in the subshell instead of in the original process and hence we get the impression that the command didn't work. We'll handle this separately in a different function and add a conditional in our `execute_commands` functions.

{% highlight python linenos %}
def psh_cd(path):
    """convert to absolute path and change directory"""
    try:
        os.chdir(os.path.abspath(path))
    except Exception:
        print("cd: no such file or directory: {}".format(path))
{% endhighlight %}

Here, we're using `os.chdir` to change the directory and we also make sure to convert the path entered by the user to an absolute path before passing it to `os.chdir`. Note that we'll have to edit our main function to add this condition.

# Pipes!
Let's get to the fun part. Pipes are a way to transfer output of one process as input to another and so on, in a chained manner. Consider this image[1] which shows how pipes are used and what they do.

![img](http://web.cse.ohio-state.edu/~mamrak.1/CIS762/unix_pipes.gif)

In essence, pipes are nothing but a pair of file descriptors which allow for read and writing. For instance, If we create a pipe, we'll have two file descriptors `f1` and `f2` where we can write stuff to `f2` and then read from `f1`. Python allows us to create pipes using `os.pipe` which returns a tuple containing the integer value of which refer to the file descriptors. Consider the implementation of our `execute_commands` function with piping below:

{% highlight python linenos %}
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
{% endhighlight %}

Let's see what we're doing here.

- __Lines 6-7:__ After checking if the pipe operator is present in the command, we create temp variables, `s_in, s_out` to hold the original values of `stdout` and `stdin`.
- __Line 11:__ Then in line 11, we store the `stdin` for our use.
- __Line 14:__ Finally, in the loop on line 14 iterates over the different commands which are piped together.
- __Lines 15-16:__ sets `stdin` to `fdin` and then closes it.
- __Lines 21-28:__ we manage the `stdout`, first we check if it's the last sub-command and if it is, create a duplicate of `stdout` using `s_out` so that the final output is redirected to the terminal. If it is not the last command i.e the output from the current command needs to stored and used as input for the next command, we create a pipe with values `fdin` and `fdout`.
- __Lines 30-33:__ We just set the `stdout` to whatever value `fdout` stores at that point.
- __Lines 30-33:__ we execute the command in question and note that when the command here is executed, it will use input from `fdin` and will write it's output to `fdout` theoretically.
- __Lines 36-39:__ We're restoring the values of `stdin` and `stdout` to their original values that we had stored earlier.
- __Lines 40:__ Execute the command normally if no pipe operators present.

# Putting it together
We have all the pieces figured out now. Let's kludge them together to get this shell working. I'm not going to paste the whole code here since that would make this post unnecessarily long, instead I have it hosted on this [repo]() so you can check it out. Once done, just provide executable permissions to the file `psh` and run it. Here's a simple example of it running.

```shell
$ ./psh
$ pwd
/home/psh
$ cat psh | wc -l
      81
```

# Conclusion
So we've written a functional shell in Python in about ~100 lines of code, that's not too bad considering we've got piping sorted out here. You can go ahead and implement the `history` command in this, check my earlier [post]() for reference. Or you can go even further and add [globbing](http://tldp.org/LDP/abs/html/globbingref.html) support. Or if you're feeling generous, add a simple addition which allows you to write comments at the prompt and doesn't actually interprets them.

Keep in mind that the shell we've implemented here should not replace your daily driver in a sense that this was written purely for the purpose of this blogpost.

---

# References

\[1]: [http://web.cse.ohio-state.edu/~mamrak.1/CIS762/pipes_lab_notes.html](http://web.cse.ohio-state.edu/~mamrak.1/CIS762/pipes_lab_notes.html)

