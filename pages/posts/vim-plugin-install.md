---
layout: post
date: 2018-06-09
title: Installing Vim plugins manually
---

When I started out with vim over an year ago, I made sure not to mess with plugins
because installing plugins seemed like such an arcane task that only a handfull of
people over at r/vim knew. This went on until I came across Pathogen, a plugin manager 
which was seemed somewhat sophisticated. I tried Pathogen and learned it enough 
to install a plugin which turned out to be quite easy.
Up until recently, while working on a personal project of mine, I came across an issue
of manually installing a plugin which intrigued me quite a bit.

First, let's understand some of the terms used in this context.

**1. Vim directory** - For GNU/Linux and macOS, it's generally `~/.vim`.
This is where vim plugins and autoload files are stored just to make everything
more organized and easy to use. Your colorschemes, plugins, and even plugin
managers are kept in this directory.

**2. `runtimepath`** - If you are familiar with what `$PYTHONPATH` in python dev environment does or
what `$PATH` in Unix does, then this is quite similar to these two. The `runtimepath`
or `rtp` is where vim looks for commands which are not defined natively such as plugin
commands or auto commands.


What really goes behind the curtains when you install a vim plugin is essentially just this.

- You write or download a vim plugin.
- place it in a folder, preferably `~/.vim/plugins/`
- Now add this path to the vim `runtimepath`
- Finally, source the plugin file


## Installation
If you've been following along, you probably have an idea now how to manually install 
a vim plugin. If not, it's alright, keep reading.
We'll be using one of my [plugin](https://github.com/danishprakash/vimport) for this example.

1 Clone the plugin to the appropriate vim directory.

```
$ git clone https://github.com/danishprakash/vimport.git ~/vim/plugins/
```

2 Update the vim runtime path. The easiest way to do this is by appending the 
plugin dir path to the runtimepath. And you can verify this by checking the value of the rtp variable.

```
:set rtp+=~/.vim/plugins/vimport
:echo &rtp
```


3 Finally, let's source the plugin file.

```
:source ~/vim/plugins/vimport/plugins/vimport.vim
```


Now you should be able to run the plugin, try this command.

```
:Vimport requests
```

--

## Conclusion
As it turns out, it's pretty simple to actually install a vim plugin. But if you are one of those who use quite a number of plugins, the management of these could turn into a nightmare pretty quick. And for the same reason, I'd rather use a plugin manager and so should you.

---
