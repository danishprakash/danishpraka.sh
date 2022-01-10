---
layout: post
title: Switching directories on Unix quickly
---

How often do you find yourself bashing `..` at the prompt in hopes of getting to the correct directory? I don't know about you but I used to do this a lot, I used to constantly switch directories only to find out I was in the wrong one or I'm a level deep and I had to immediately back-up `..`.
So, I started looking for ways that would help me switch directories more easily. I came across this tool [`z`](https://github.com/rupa/z) which is a good alternative but It didn't felt intuitive enough, you had to hope it would guess the right directory.

I came up with a simple trick which has worked good enough for me for quite some time now, it's intuitive and configurable.

# Function
This is a simple bash function with `find` and `fzf`. Load this up in your `.zshrc`. Follow along to get a grip on how this actually works. 

{% highlight shell linenos %}
function quick_find () {
    dir=$(find ~/programming -type d -not -path '*/\.*' -maxdepth 1 | fzf)
    cd $dir
    zle reset-prompt
}
{% endhighlight %}

Let's go over each and every element in the function defined above.

1 `find`: find helps you find files and directories on your system. Here, we're doing a search for all the directories (`-type d`) in the `programming` directory (this is just me, you can add more directories in which you want to lookup). Next, we're making sure that hidden directories don't show up (`-not-path '*/\.*`). And finally we make it a rule that the depth to which find should look for directories is just 1 level deep, that means it won't go into a subdirectory, say `subdir` which resides `~/programming/dir/subdir`, which is actually 2 levels deep.

2 [`fzf`](https://github.com/junegunn/fzf): You probably already know about `fzf` but if you don't, it's a fuzzy file finder and it is really fast. We pass the results from `find` which is nothing but a list of directories to `fzf` which opens up a nice little interface where we can get suggestions as soon as we start typing, refer to the [gif](#conclusion) below.

3 `cd $dir`: Finally, `cd` into the selected directory. A note here, you need to hit the control return (enter) key for the cd to actually take effect, I've been looking into the why of this but couldn't find a plausible explanation. Hit me up if you have something of value in this context. 

__Update__: Thanks to [/u/maji_yabakune](https://www.reddit.com/user/maji_yabakune) for helping with a solution to `cd`ing into the directory without hitting the return key, explained below.

4 `zle reset-prompt`: This redraws the prompt to take into immediate effect the new working directory so you don't need to hit the enter key anymore.


# Creating a shortcut
Now, we would like to have a handy key combination to open our switcher, how about `Ctrl-p`? We would want our function to fire up as soon as we type `Ctrl-p`, so a simple bindkey should do, right? Well, no, zsh doesn't allow you to bind keys to a function, instead we would create a widget which maps to the function and finally bind that widget to the key combination. We can do that by creating a widget using the zsh line editor, `zle` and then we can specify our key combination mapped to this widget we just created.

{% highlight shell linenos %}
zle -N quick_find_widget quick_find
bindkey "^p" quick_find_widget
{% endhighlight %}


That's about it, simply put the [function](#function) and these two lines in your `.zshrc` and you're good to go.

--

# Conclusion
If all goes well, you should have something like the gif below making it easier for you to switch between directories easily. 

![img](https://i.imgur.com/r8eWY0L.gif)

Also, if you can think of improvements to this, please open an issue and/or a PR on [this](https://github.com/danishprakash/dotfiles) repository, there is more stuff there. Or if you have other such handy tricks, do let me know. Feel free to contact me via email.

---
