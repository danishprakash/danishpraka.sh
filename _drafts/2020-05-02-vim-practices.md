---
layout: post
title: Vim Practices
---

# Introduction
Using any tool for a prolonged period of time, you develop/figure out/discover certain workflow helping you do your work more efficiently. I've been using (n)Vim for more than 2 years now and needless to say, I have discovered quite a lot of such practices that are now indispensable to my workflow. I talk about them in this post.

# Search and replace using dot
`/search` for something, then hit enter to activate the search pattern and land on the searched for item, hit  \`\` to go back  to where you were before so that the substitution will come into effect for the first search result. Hit `cgn` to make changes to the selection. You can now hit `.` to repeat the change for subsequent search results.

# Replace word in a buffer
Easiest way to copy a word and then paste it in place of another word is to first yank the first word using `yaw` and then moving to the place where you want to paste the word you just copied. Now, if its'a word, just do a visual selection on it `vaw` and then hit `p`.
