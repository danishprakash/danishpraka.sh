---
layout: post
title: Distribute your application via Homebrew
---

I was confronted with a problem when I was writing the documentation of a command-line application I recently wrote, [`goodreadsh`](https://github.com/danishprakash/goodreadsh). The problem was how to allow users to install my application, should I ask them to `curl` the script and add it to their `PATH` and finally give it executable permissions? Because that is precisely how I've done it for a few applications I've built in the past. Then it hit me, I could atleast do my fellow mac users a favor and have my application available via homebrew. Not that there's anything wrong with having to install an application manually, I still do that often but typing 2 trivial commands instead of 4 seems like a sensible move.

There are essentialy two steps in this process:

- Writing a formula for your application.
- Creating a tap to host your formula file.

Don't worry about the terminology just yet, we'll get to know them as and when required.

# Your application's `tar` archive
Homebrew accepts a tar archive of your application in order to process it. We can generate one by simple creating a new release on your project's github repository. Once you've successfully created a release, click on the releases tab and find the link to the tar archive below the release label. My application's [release(s)](https://github.com/danishprakash/goodreadsh/releases) for example.

# Write your formula
Homebrew formulae are essentially ruby scripts which stores information about your application. It tells homebrew important information regarding the installation of your application like where and how your app is going to be installed. This is what a simple formula for an application written in bash would look like.

{% highlight ruby linenos %}
class Goodreadsh < Formula
	desc "Command-line interface for Goodreads"
	homepage "https://github.com/danishprakash/goodreadsh"
	url "https://github.com/danishprakash/goodreadsh/archive/1.0.1.tar.gz"
	sha256 "63d1de17449611f1490b1930e63cc8890f9f10c7e317f02c901e6a79236c10e2"
	head "https://github.com/danishprakash/goodreadsh.git"

	def install
		bin.install "goodreads"
	end

	test do
		system "#{bin}/goodreads"
	end
end
{% endhighlight %}


Now, almost all of the fields here are pretty much self-explanatory but we'll go through them quickly.

- `desc`: small description of your application, make sure you don't end it with a period (.)
- `homepage`: a webpage for your project, if you don't have one, the project's github repo will do. 
- `url`: this is the url of your application's tar archive. Use the project's github repo if you don't have one.
- `sha256`: this is the `sha` value of your application's tar for authentication. You can calculate the `sha` value of your application using the command `openssl dgst -sha256 <(curl -s -L <URL>)` where `URL` is the link to the tar archive to your application.
- `head`: a link to your github repo since Homebrew can understand several vcs, this option is sometimes used to install your application using the `--HEAD` option for development purposes.

<br>
You can use this template or you can generate a formula of your own. Homebrew provides a simple command for this. `brew create <URL>`

{% highlight shell %}
$ brew create https://github.com/danishprakash/goodreadsh/archive/1.0.1.tar.gz
{% endhighlight %}

The `URL` in question is the link to the tar archive of your application. I'm using the one created automatically by Github when you create a new release and/or tag. As soon as you execute this command, an editor will open up with the formula.

You can check whether your formula is working or not by installing your application from specifying the formula.

{% highlight shell %}
$ brew install --build-from-source <formula.rb>
{% endhighlight %}

If it works, good enough. Now make sure your formula abides by the guidelines defined by homebrew using this command. Rectify any errors or warnings if there.

{% highlight shell %}
$ brew audit --strict <formula.rb>
{% endhighlight %}


# Install & Test
Since this is a rather trivial application that we're writing a formula for, the formula for this would also be a simple one. You can have multiple things defined in your formula depending upon what you expect it to do.

Moving ahead, we can see a function definition `install` in which there's a single expression `bin.install "goodreads"`. This will move the file in double quotes into the Formula's bin directory and make it executable (`chmod 0555 goodreads`).

Similarly in the second function definition `test`, we execute the installed executable with the `system` command in ruby which is used to execute commands from within ruby scripts. The `system` function takes a single quoted argument which is the absolute path to the executable. 

# Putting it together
Before moving one, there's one thing I'd like to make clear. There are more than one way to allow users to allow installing your application via homebrew. First, having your application formula in the `homebrew-core` repository and the second is creating a tap. Having your application formula accepted in `homebrew-core` isn't very straightforward since there are various rules that determine whether a package should be in the `homebrew-core` repo, for instance, your application's Github repo should have more than 30 watchers, 75 stars and 30 watchers and should be more than 30 days old.

Taps on the other hand are your own personal formula repository where formula(e) for your applications can be stored. Homebrew can look up formula(e) from this repo and allow you to install the said application. In this tutorial, we'll be creating a tap. Now, let's create a repository where we'll store our homebrew formulae, let's call it [`homebrew-formulae`](https://github.com/danishprakash/homebrew-formulae) and add our formula file here. 

We can now install the application via homebrew. But before doing that, we need to tell homebrew where to find our application since it is not there in the `homebrew-core` repository. We can do this by the tap command. And installing our application afterwards.

{% highlight shell %}
$ brew tap danishprakash/homebrew-formulae
$ brew install goodreadsh
{% endhighlight %}

Another upside to having a designated formula repo (tap) of your own is the simple fact that you can simply add another formula in the future and have it installed in the same way. So this acts like a collection (repo?) of all your application's formulae making it easier to maintain and update.

--

# Conclusion
Hopefully you can now write a homebrew formula for a trivial application and distribute it via homebrew by creating a tap.
There are lots of options for you to consider when you write a formula for your application in the Homebrew [Formula Cookbook](https://github.com/Homebrew/brew/blob/master/docs/Formula-Cookbook.md). I'd suggest taking a good look at the formula cookbook before attempting to write your own formula.

---
