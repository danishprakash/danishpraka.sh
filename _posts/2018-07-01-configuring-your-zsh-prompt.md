---
layout: post
title: Git branch in vanilla zsh
---

Recently the thought of having the current branch indicated on my zsh prompt hit me, when I looked up for solutions, I was greeted with the idea of installing one of the frameworks for zsh which obviously was not my cup of tea. I then looked up for other solutions which sort of worked but sometimes broke unexpectedly. I came up with a simple solution that has been working great for me for the past month or so in my vanilla zsh setup.

When I say vanilla zsh, I meant to say we are not going to use any of the fancy frameworks available for zsh namely `oh-my-zsh` or `prezto`.
I personally avoid using such frameworks that add unnecessary overhead to your tool wherein the functionality you're seeking can easily be added via simple configurations.

__Note__: If you are just looking for the solution, jump to [Conclusion](#conclusion) directly and read on if you don't mind bits of interesting info thrown around.

# Git branch
Before I started looking for solutions for this particular problem, I only knew one way to echo the current branch in a directory which is the good old `git branch` command. But turns out there's one more and possibly others.

```bash
$ git symbolic-ref HEAD
```

From the official documentation, `git symbolic-ref <name>` reads which branch head the given symbolic reference refers to and returns the full path to it relative to the `.git` directory. In other words, when you give `HEAD` as an argument to `git symbolic-ref`, it will return the path of your working directory. Using this output, it's easy to determine which branch we are currently on.

```bash
$ git symbolic-ref HEAD
refs/heads/master
```

I'm using the latter version since it will give us a rather brief and static output than `git branch` which would list all the branches there are in your current working tree.

# Suppressing errors
In directories which are not git repositories, our command will throw an error. To supress such errors, we could simply redirect the error. Our updated command:

```bash
$ git symbolic-ref HEAD
fatal: Not a git repository (or any of the parent directories): .git

$ git symbolic-ref HEAD 2> /dev/null
```

The `2> /dev/null` redirects the `stderr` or standard error to a special file `/dev/null` which takes input but doesn't really do anything with it. So we're sorted here. Read more about standard streams [here](http://www.learnlinux.org.za/courses/build/shell-scripting/ch01s04.html).

# Comes in `awk`
You certainly don't need `ref/heads/master` in your prompt, let's filter the unwanted stuff out. We'll use a simple awk script (command really) to do the job.

```bash
$ git symbolic-ref HEAD 2> /dev/null | awk 'BEGIN{FS="/"} {print $NF}'
master
```

That looks about right. Let's get this onto our prompt.

# Updating prompt
Now that we have all the inputs ready, let's put these together to get it working. Add this function in your `.zshrc`, preferably on the top so that it becomes easier for you to re-use it.

```bash
function git_branch() {
    branch=$(git symbolic-ref HEAD 2> /dev/null | awk 'BEGIN{FS="/"} {print $NF}')
    if [[ $branch == "" ]]; then
        :
    else
        echo ' (' $branch ') '
    fi
}
```

Here, we initialize a `branch` variable with the value of the output of the command we put together in the steps above. If you are wondering why we have the command enclosed inside `$()`, this is called command substitution wherein a command is replaced by it's output. So we'll be left with the actual branch name in the variable `branch`. The conditional logic after that is used to handle cases where the current directory isn't really a git repository and we don't want to leave the prompt untouched.

```bash
setopt prompt_subst
PROMPT='%~ $(git_branch) >'
```

Here, we set the `prompt_subst` option in our zsh, this allows command substitution to be able to be performed in prompts. In other words, we defined a custom command named `git_branch` which is then used in our shell prompt since functions in shell scripts are essentially commands that can be executed from the shell. Now the shell performs command substitution everytime the prompt appears on the terminal. After this we set the prompt using the `PROMPT` shell variable. The `%~` will be expanded to the current working directory.

Finally, source your `.zshrc` file to see the changes take effect. Your prompt should look like this assuming you are inside a directory which is a git repository and is on the `master` branch.

```bash
$ ~/new_directory/sample_git_repo (master) >
```

--

# Conclusion
So, having the current branch displayed on your zsh prompt was all in all a simple `git` command with a pint of `awk` in it and a simple shell script. For those restless souls who landed here in search of the solution, here it is.

```bash
# function to return current branch name while suppressing errors.
function git_branch() {
    branch=$(git symbolic-ref HEAD 2> /dev/null | awk 'BEGIN{FS="/"} {print $NF}')
    if [[ $branch == "" ]]; then
        :
    else
        echo ' (' $branch ') '
    fi
}


setopt prompt_subst             # allow command substitution inside the prompt
PROMPT='%~ $(git_branch) >'     # set the prompt value
```
