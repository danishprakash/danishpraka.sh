---
layout: post
title: Recovering lost commits
---

So, you've been working on this project of yours, you are on the master branch and at some point in time, for some reason, you decided to go back to a commit. Without even realising, you make some changes and then you do `git checkout master`, then you do `git status` and finally you realise you've messed up big time.

This happened to a friend of mine recently while he was working on a big project, after we started looking for solutions, there were times when it seemed like the changes would have to be done again manually for every file. But git had us covered in a sense that git never loses anything, ofcourse unless you do `git gc`, and you can almost always recover your lost stuff.

# Detached HEAD
When you checkout a previous commit on a branch, say `master`, you are not on any branch, instead you are in a state called `detached HEAD`. This is somewhat confusing but it actually makes sense. Think of it this way, going back into history and changing something there may result in a conflict.

# Dangling commits
The commits you've made while in a `detached HEAD` state are called dangling commits because they don't belong to a branch. After you've checked out a branch and are no longer in a detached HEAD state, you may think you've lost the dangling commit but it is not quite right. Dangling commits can be located in many ways, two of which are:

1. `git fsck --lost-found`: It identifies all the dangling commits and writes them to the directory `.git/lost-found/commit` and to `stdout`. It may not be the best way to identify dangling commits since it just shows the commit hash and not the commit message.

2. `git reflog`: It keeps track of all the `refs`, which are references to commits, in your local directory. Hence the name `reflog`. It is highly unnlikely that your lost commit wouldn't here. You can sift through the output to find your lost commit and then copy it's hash. 

# Applying commit
After copying the commit hash obtained from `git reflog`, we can simply do `git merge <hash>` to apply the changes to our current branch. But make sure you are on the master branch before doing this otherwise we're back at square one.
<br>
<br>

---

# Conclusion
We can easily recover a lost commit using these steps. Although there might be other cases where this may not be applicable.

- Use `git reflog` to find the lost commit.
- Copy hash of the lost commit.
- Do `git merge <commit_hash>`

{% highlight shell %}
$ git reflog
# copy lost commit's hash

$ git merge <hash>
{% endhighlight %}

You can repeat this process for a number of commits that you've "lost" but make sure you are on the correct branch before actually going ahead and merging the commits.
<br>

---
