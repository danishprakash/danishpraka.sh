---
layout: post
title: Manually installing vim plugins
---

![img](https://res.cloudinary.com/practicaldev/image/fetch/s--NIE-92PW--/c_limit%2Cf_auto%2Cfl_progressive%2Cq_auto%2Cw_880/https://i.imgflip.com/1teh21.jpg)

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

**2. runtimepath** - If you are familiar with what `$PYTHONPATH` in python dev environment does or
what `$PATH` in Unix does, then this is quite similar to these two. The `runtimepath`
or `rtp` is where vim looks for commands which are not defined natively such as plugin
commands or auto commands.


What really goes behind the curtains when you install a vim plugin is essentially just this.

- You write or download a vim plugin.
- place it in a folder, preferably `~/.vim/plugins/`
- finally you add this path to the vim `runtimepath`


# Installation
If you've been following along, you probably have an idea now how to manually install 
a vim plugin. If not, it's alright, keep reading.
We'll be using one of my [plugin](https://github.com/prakashdanish/vimport) for this example.

1 Clone the plugin to the appropriate vim directory.

```bash
git clone https://github.com/prakashdanish/vimport.git ~/vim/plugins
```

2 Update the vim runtime path. The easiest way to do this is by appending the 
plugin dir path to the runtimepath.

```vim
:set rtp+=~/.vim/plugins/vimport
```

And you can verify this using 

```vim
:echo &rtp
```

Now you should be able to run the plugin, try this command.

```vim
:Vimport requests
```

This maybe a rude awakening as to how plugins are managed by the so called plugin managers out there, it was for me.
Nonetheless, plugin managers provide us with one command substitutions for all of the above
and a lot more.

---
