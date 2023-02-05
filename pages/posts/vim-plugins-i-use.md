---
layout: post
date: 2018-06-30
title: Vim plugins I use
---


<span class="note">Head to the discussion over at [Hacker News](https://news.ycombinator.com/item?id=17430546), there's quite a lot of good advice there.</span>


I'm an advocate of using vanilla vim or neovim. But there are times wherein you feel the need to install plugins, after working on vim for the past couple of months religiously, I've come across certain plugins that I feel help me in my dev workflow. Although there are some plugins that I've mentioned in this article whose functionality can easily be added by configuring my .vimrc but I think if a plugin helps you save time that'd be rather spent configuring the setup, you're better off using the plugin.

This post should not be seen as one of those *"Must have plugins for vim"* but rather as a post describing the plugins I use and why I use them, and how they help me with my developer workflow. Using or not using these plugins is something for you to decide. 

__Note:__ I'm using [vim-zen](https://github.com/danishprakash/vim-zen) as my plugin manager, It's a lightweight barebones vim plugin manager with multithreading (python). You can learn more about it [here](https://github.com/danishprakash/vim-zen).

1. [__junegunn/goyo.vim__](https://github.com/junegunn/goyo.vim)<br>
It helps transform vim into a minmalistic looking note taking application. I mostly use it while write markdown for my blog. In essence, this plugins disables numbers, the statusline and other elements from the editing window leaving you with just the text.

2. [__airblade/vim-gitgutter__](https://github.com/airblade/vim-gitgutter)<br>
I use it for just one simple reason, It shows me the lines where unstaged changes are present and the type of change that has been done (+, -, ~). This comes in very handy when I'm about to push some changes and I can quickly jump through parts of code where changes have been made.

3. [__tpope/vim-surround__](https://github.com/tpope/vim-surround)<br>
This is useful where you need to wrap a word or a text block inside quotes or tags. For instance, wrapping a long string of text inside the parens of a method call wherein you forgot to put quotes around the actual string. The command `ysi('` would do the job.

4. [__townk/vim-autoclose__](https://github.com/townk/vim-autoclose)<br>
Simply completes characters which work in pairs, for instance, as soon as I type in a `(` vim will automatically add `)` and put the cursor in between.<br>
`(  -->  (|)`

5. [__tpope/vim-commentary__](https://github.com/tpope/vim-commentary)<br>
Works in a similar way as vim-surround but instead, as the name suggest, it comments out the area specified by the motion.It makes commenting out your code a breeze.<br><br>
For instance, `gcG` -> comments out contents of the file from current cursor position to end of file. You can use it with a lot of other motions.

6. [__morhetz/gruvbox__](https://github.com/morhetz/gruvbox)<br>
This is the colorscheme that I've been using for quite a while now. I'm using the same scheme with iTerm2 as well. This is how it looks with a vimscript file open. <img src="https://imgur.com/TQpjlUI.png" alt="drawing" width="600px"/>


7. [__junegunn/fzf__](https://github.com/junegunn/fzf)<br>
A fuzzy finder which helps finding files really QUICKLY. Just enter `FZF` as an ex-command and It'll open up a small window with all the files there in your working directory. Start typing out the file name and see it bring up the matching file names in a jiffy. I have it mapped to `Ctrl-t` to quickly open it up while editing stuff.

8. [__scrooloose/nerdtree__](https://github.com/scrooloose/nerdtree)<br>
It's a file system explorer that sits inside your vim editor. Think of this as the the file explorer in editors like VSCode and SublimeText. Although I don't use Nerdtree pretty often to open files but I like to have the directory structure visible to me while I'm working. 

9. [__ervandew/supertab__](https://github.com/ervandew/supertab)<br>
This allows you to use `Tab` to autocomplete keywords. Note that this uses vim's native completion feature and not any of it's own. This is not similar to YCM in any way.

10. [__danishprakash/vimport__](https://github.com/danishprakash/vimport)<br>
This plugin helps you quickly import and drop python packages and/or modules that you've imported in your project. I use it when I'm working on python projects wherein I'm adding and removing modules on a rolling basis.

--

# Updates 
I'll keep this list updated with new plugins that I install or remove plugins from the list above if I find a good enough alternate for it within vim itself or another plugin which might offer better features. 


---
