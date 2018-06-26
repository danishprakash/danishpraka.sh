---
layout: post
title: Vim plugins I use
---

I'm an advocate of using vanilla vim or neovim. But there are times wherein you feel the need to install plugins, after working on vim for the past couple of months religiously, I've come across certain plugins that I feel help me in my dev workflow. Although there are some plugins that I've mentioned in this article which can easily be replace by adding some configuration in my .vimrc but I think if a plugin helps you save some time that'd be rather spent configuring the setup, you're better off using the plugin.

__Note:__ I'm using [vim-zen](https://github.com/prakashdanish/vim-zen) as my plugin manager, It's a lightweight barebones vim plugin manager with multithreading (python). You can learn more about it [here](https://github.com/prakashdanish/vim-zen).

1. [__junegunn/goyo.vim__](https://github.com/junegunn/goyo.vim)<br>
It helps transform vim into a minmalistic looking note taking application. I mostly use it while write markdown for my blog.

2. [__airblade/vim-gitgutter__](https://github.com/airblade/vim-gitgutter)<br>
I use it for just one simple reason, It shows me the lines where unstaged changes are present and the type of change that has been done (+, -, ~).

3. [__tpope/vim-surround__](https://github.com/tpope/vim-surround)<br>
This is useful where you need to wrap a word or a text block inside quotes or tags. For instance, wrapping a long string of text inside the parens of a method call wherein you forgot to put quotes around the actual string. The command `ysi('` would do the job.

4. [__townk/vim-autoclose__](https://github.com/townk/vim-autoclose)<br>
Simply completes characters which work in pairs, for instance, as soon as I type in a `(` vim will automatically add `)` and put the cursor in between.<br>
`(  -->  (|)`

5. [__tpope/vim-commentary__](https://github.com/tpope/vim-commentary)<br>
Works in a similar way as vim-surround but instead, as the name suggest, it comments out the area specified by the motion.<br>
`gcG` -> comment out contents of the file from current cursor position to end of file. 

6. [__morhetz/gruvbox__](https://github.com/morhetz/gruvbox)<br>
This is the colorscheme that I've been using for quite a while now. I'm using the same scheme with iTerm2 as well.


7. [__junegunn/fzf__](https://github.com/junegunn/fzf)<br>
A fuzzy finder which helps finding files really QUICKLY. Just enter `FZF` as an ex-command and It'll open up a small window with all the files there in your working directory. Start typing out the file name and see it bring up the matching file names in a jiffy. I have it mapped to `Ctrl-t` to quickly open it up while editing stuff.

8. [__scrooloose/nerdtree__](https://github.com/scrooloose/nerdtree)<br>
It's a file system explorer that sits inside your vim editor. Think of this as the the file explorer in editors like VSCode and SublimeText. 

9. [__ervandew/supertab__](https://github.com/ervandew/supertab)<br>
This allows you to use `Tab` to autocomplete keywords. Note that this uses vim's native completion feature and not any of it's own. This is not similar to YCM in any way.

10. [__prakashdanish/vimport__](https://github.com/prakashdanish/vimport)<br>
This plugin helps you quickly import and drop python packages and/or modules that you've imported in your project.

# Updates 
I'll keep this list updated with new plugins that I install or remove plugins from the list above if I find a good enough alternate for it within vim itself or another plugin which might offer better features. 

