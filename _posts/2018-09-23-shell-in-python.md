---
layout: post
title: Writing a shell in Python
---

One of the first posts I wrote on this blog of mine was [Write a shell in C](https://danishprakash.github.io/2018/01/15/write-a-shell.html). It described how to write a functional shell for \*nix based systems. When I was undertaking that project, I wanted to do the same in Python and for some reason that I can't remember right now, I chose C when in reality I was working on Python almost all the time. A recent discussion with a friend of mine lead me to write this post and since I started, it turns out that it is really easy to do this in Python which is true for most of the things with Python.

We'll write a simple shell that that will support almost all the basic commands. We'll also implement piping for our shell which will allow us to pipe the output of a command as an input to another command. 

# Flow
In the `main` function, we'll handle the program flow.  First, let's get the user input, pretty simple, we'll run an infinite loop and prompt the user for an input.

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
We can handle `exit` command simply by breaking out of the loop. Next, we need to execute the command entered by the user. We'll manage the execution in a separate function, let's call that `execute_commands(command)`. Also, while we're at it, let's add a simple `help` function to let the user know what's actually happening.

# Executing commands
Let's execute the commands entered by the user. As stated earlier, we are going to be doing this in a separate function. We are going to be using the `subprocess` builtin module, `import subprocess` and we're good to go. The `run` function in particular is used to run system commands in a subshell. For the C people, this saves us from going about forking and creating a child process and then waiting for the child to finish execution, let Python take care of that this one time.

```python
def execute_commands(command):
    try:
        subprocess.run(command.split())
    except Exception:
        print("psh: command not found: {}".format(command))
```
We're going to make sure that our shell doesn't come crashing down if the user enters `cs` instead of `cd` by mistake hence the `try/except` mechanism. Note that there are many other methods to run system commands from within Python including `os.system` and `commands` etc but using `subprocess` is the [preferred](https://docs.python.org/2/library/commands.html) [way](https://docs.python.org/3/library/os.html?%20system#os.system) of doing this.

# Changing the directory

# Pipes!

# Help and Exit

# Conclusion
