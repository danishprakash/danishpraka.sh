---
layout: post
title: Bash Scripting Practices
---

# What?
We've been using runc at work in production for a while now and although it seemed somewhat obscure at first, we have come around to being used to it so much so that it seems more intuitive than docker, but that may be an exaggeration. I wanted to write this blogpost as a gentle introduction to runc especially when you are starting out because I remember all there was around runc back then was the source repository and a few talks from Aleksa Sarai.

# Debugging

{% highlight sh linenos %}
set -o xtrace
{% endhighlight %}

We've been using runc at work in production for a while now and although it seemed somewhat obscure at first, we have come around to being used to it so much so that it seems more intuitive than docker, but that may be an exaggeration. I wanted to write this blogpost as a gentle introduction to runc especially when you are starting out because I remember all there was around runc back then was the source repository and a few talks from Aleksa Sarai.

# Flags
full flags instead of shorthands (--recursive) [readability]

# Logging
setting up a simple logging mechanism

# Command line flags
parsing command line arguments (shift operator)

# Syntax
diff bw [[]] and [] and (())

---
