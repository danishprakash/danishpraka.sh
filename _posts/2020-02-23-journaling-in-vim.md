---
layout: post
title: Journaling in Vim
---

<span class="note">UPDATE: This post has been updated with some really good suggestions from people over at [r/vim](https://www.reddit.com/r/vim/comments/f8a3jf/journaling_in_vim/).</span>

I journal daily(not anymore) but I'm not a fan of using pen and paper although they are supposed to be better at this task. There are two reasons for this, first, digital note taking is easier to organize and get back to and second, at some point in time, I'd like to do a textual analysis on my journalling data (r/dataisbeautiful).

In order to make the process as painless as possible, I've created a setup for journalling using Vim which has been working really good for me lately. I'd walk you through my setup in this post.

# Basics
I use markdown formatting for writing most of my documents including my journals and other notes since they are easy to format, are used universally and have good support by most applications be it web or desktop. You can easily export them to a plethora of document types, LaTeX flavored PDF being one of them.

Secondly, the choice of editor despite the title, is [(neo)vim](https://neovim.io/), if you're reading this article, you probably know the difference between the two, even if you don't, it wouldn't really affect anything you might get out of this article, so read on :D

With that out of the way, let's move on to some more interesting pieces of this setup.

# Vim templates
A template in Vim is a simple `.skeleton` file which can be used to populate buffers based on certain rules. For instance, if you find yourself adding the shebang header to every shell script you write, you can "automate" it using a skeleton file so that everytime you open a `.sh` file, your buffer will be preloaded with the text you've specified inside the `.skeleton` file, which could very well be just the following:

{% highlight text %}
#!/usr/bin/env bash
{% endhighlight %}

You can create your own templates and place them in a directory, I prefer the `~/.config/nvim/` directory itself just so that all the configuration files remain together. I have kept my journal template very simple with the following contents:

{% highlight text %}

## What went wrong today?


## What went right today?

{% endhighlight %}

We're going to add one more piece to it later on in the post but this is mostly it. As I mentioned above, you can have it your way, this is just how I prefer to write my journal everyday.

# Autocommands
Autocommands are a great way to automate functionality in vim. Here, we'll use `autocmd` to populate our buffer from our skeleton file when the buffer metadata matches a certain pattern. My journal directory looks something like this:

{% highlight text %}
journal/
├── 2019
│   └── 01
│   └── 02
│   └── 12
└── 2020
    └── 01
    └── 02
{% endhighlight %}
And for the same, I require that every `.md` file that I open inside `~/journal/*` should be populated with my journal template. We can do that by using the following autocmd:

{% highlight vimscript linenos %}
autocmd VimEnter */journal/**   0r ~/.config/nvim/templates/journal.skeleton
{% endhighlight %}
The above autocommand is triggered on the `VimEnter` event i.e every time you enter vim from the command line. It is triggered on the pattern `*/journal/**` which recursively matches it's subdirectory. Finally, it reads and populates the active buffer with the journal template using the `r`(read) command.

We'll also wrap our autocommand(s) in an `augroup` which helps removing and executing a group of autocommands together, it also makes it easier to organize your autocommands and eventually your vimrc. We'll add more autocommands to the journal augroup as shown below:

{% highlight vimscript linenos %}
augroup journal
    autocmd!

    " populate journal template
    autocmd VimEnter */journal/**   0r ~/.config/nvim/templates/journal.skeleton
augroup end
{% endhighlight %}

That looks much more readable, we will add subsequent autocmds to this augroup.

# Completion
Another important piece here is the completion source. For instance, a month into your journaling journey, you will be repeating or referencing a lot of words whether that's names of people, places or some technical jargon related to work. In order to minimize the effort and keystrokes required to repeat such words, we can make use of vim's completion feature which allows us to select custom sources. We can set a custom completion source by setting an appropriate value for the `complete` option:

{% highlight vimscript linenos %}
autocmd VimEnter */journal/**   setlocal complete=k/Users/danish/journal/**/*
{% endhighlight %}
The interesting thing to note in the above command is the `setlocal complete=...` command being triggered upon opening a new/existing file which matches the glob pattern specified. The `k` char before the file path tells vim to scan and source words for completion from the path that is specified local to the buffer matching the pattern and event. I urge you to read more about this on the [help document](http://vimdoc.sourceforge.net/htmldoc/options.html#'complete'), there are a bunch of potentially other useful flags for this option. 

Note: In order to get Vim to scan the files recursively, this [answer](https://stackoverflow.com/questions/12094708/include-a-directory-recursively-for-vim-autocompletion) pointed me to the right globbing pattern to use.

# Header
I write the present day's journal the next morning, so in the morning when I open Vim to write the previous day's entry, I like to have the date populated there along with the templated content, something like this:

{% highlight text %}
# 22-02-2020


## What went wrong today?


## What went right today?

{% endhighlight %}

Since this is dynamic, we can't make use of Vim templates here. Instead, let's use a combination of the shell and some Vimscript here. First off, I have created the following alias in my shell:

{% highlight sh linenos %}
journal='nvim $(date -v-1d "+%d-%m-%Y").md'
{% endhighlight %}
Using simple command substitution and the date utility, this will open (n)vim with the filename of the buffer as the previous day's date. For instance, If I'm writing the previous day's entry today (23/02/2020), the filename would aptly be named `22-02-2020.md`.

Now, as soon as this command is executed, our templating autocommand, which we had setup previously, will spring into action and will populate the buffer with our skeleton file. To add the header, which is now the filename itself, we will use some good'ol Vimscript:

{% highlight vimscript linenos %}
" set header title for journal & enter writing mode
function! JournalMode()
    execute 'normal gg'
    let filename = '#' . ' ' . expand('%:r')
    call setline(1, filename)
    execute 'normal o'
    execute 'Goyo'
endfunction
{% endhighlight %}

We get the filename minus the extension, prepend a hash to that so that it formats as a markdown header and set that to the topmost line of our buffer. We then move on to the next line and then enter focus/zen mode provided by the [junegunn/goyo](https://github.com/junegunn/goyo.vim) plugin. Let's also add this to our journal augroup so that it does it's job at the right time:

{% highlight vimscript linenos %}
" workflow for daily journal
augroup journal
    autocmd!

    " populate journal template
    autocmd VimEnter */journal/**   0r ~/.config/nvim/templates/journal.skeleton

    " set header for the particular journal
    autocmd VimEnter */journal/**   :call JournalMode()

    " https://stackoverflow.com/questions/12094708/include-a-directory-recursively-for-vim-autocompletion
    autocmd VimEnter */journal/**   set complete=k/Users/danish/programming/mine/journal/**/*
augroup END
{% endhighlight %}

Our journal augroup now looks complete with all the configuration we talked about in the previous sections.

# Appearance
This is purely subjective, you may or may not decide to read this but I decided to add this section purely for posterity.

I don't use syntax highlighting, I've come to realize that It's much easier to focus for me without the colors and text formatting involved. I made a [monochrome theme](https://github.com/danishprakash/vim-yami) just to help me with the transition from a lot of colors to none and shortly after, I disabled syntax highlighting altogether. Aside from that, here's how my setup looks once I enter the `journal` command in the respective directory:

<img src="./../../../assets/img/posts/journaling-in-vim-preview.png" width="570px"/>

# Conclusion
This is just a way to remove a little resistance from the process of daily journaling by automating some of the parts in a way that all that is required from you is just the writing part which is how it should be. But again, this varies widely from person to person but I'm sure there's something or the other you can pickup from this post. There are bound to be errors/mistakes in the article or a way to better the process, if that's the case, reach out!

---
