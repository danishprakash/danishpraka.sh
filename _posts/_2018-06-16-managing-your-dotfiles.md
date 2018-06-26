---
layout: post
title: Managing your dotfiles
---

Back when I started using vim, I used to hear this term dotfiles a lot, almost everywhere. Then soon after, I had my own messy yet my own .vimrc. I used to copy stuff into it from everywhere, every repo I found online, every article, every SO answer. It got to a point that It became really problematic for me to properly understand my own .vimrc. Then, once while reading this great article by Doug Black, I came across this great advice, 

_"Never put things in your .vimrc file that you don't understand."_

I immediately stripped down my vimrc in a jiffy, but that was not enough, because by now things that were trivial in their own sense seemed some sort of mystical wizardry. So I did what I should've had done way back, I started from scratch. Soon after that, I had a decent vimrc of my own which comprised of configs I added day in day out as I worked my way towards vim. It once occurred to me to have my own vimrc repo on github, I didn't really knew the use of it, but back then I thought it was all show. So I made a repo and put in all my configs in it. But updating that repo became a problem, everytime I made changes to my configs, I had to manually cp the files to a dotfiles/ directory and then do a git push.

Turns out It's pretty easy for you to manage your dotfiles. For the rest of this post, I'll walk across how I go about managing my dotfiles on my machine.
