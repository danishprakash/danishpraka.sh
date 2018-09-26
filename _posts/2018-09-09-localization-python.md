---
layout: post
title: Localization in Python
---


Localization is a big deal especially when your application is being used by a lot of people from different parts of the world. It is the process of making your application available in a local language. You don't want to exclude a specific portion of your ever growing user base just because your application does not support their native language. Localization is a great way to show your users that you care about them. I mean, it strikes a personal chord. This can be exemplified by the recent [hullabaloo](https://economictimes.indiatimes.com/small-biz/startups/newsbuzz/browse-in-hindi-on-amazon-india/articleshow/65679424.cms) over Amazon releasing a hindi version of their application in order to provide an extremely personalized experience to their Indian users and to target the next 100 million.

I've been writing Python for a while now and I was working on this big open source project recently, trying to fix a trivial issue which ended up failing the builds. When I inquired about it, it turns out that the builds failed because I forgot to make the strings in my changes __translatable__. So, I set about looking for answers and there it was, Localization. In this post, we'll walk our way towards providing translations to a simple python program.

# GNU gettext
There are other ways with which you can provide localization for your applications. But we'll use the `gettext` module for the purpose of this post. It provides internationalization and localization services for your applications and comes bundled with the standard python installation. It exposes two different API's for you to work with, a more standard `gettext` API which affects your entire application's translations and a class-based API which is more suitable for Python modules and applications. We'll make use of the latter.

# Hello World!
We'll use this [legendary](https://blog.hackerrank.com/the-history-of-hello-world/) hello world program in this post with a simple addition.

{% highlight python linenos %}
def main():
    print("Hello World!")
    print("Localization is fun!")

if '__main__' == __name__:
    main()
{% endhighlight %}

# Translations
In order to provide the translations which could be read by the `gettext` module, we need to create a separate directory named `locales`, this can be named anything as long as it's intuitive. For the sake of keeping this post brief, we'll be providing a German(Deutsch) translation for our `Hello World` program. For the same, our `locales` directory would look something like this.

```text
locales/
├── de
│   └── LC_MESSAGES
└── en
    └── LC_MESSAGES
```

Where `de` and `en` are language codes for german and english respectively. You can find a list of all the languages and their respective language codes [here](https://www.science.co.il/language/Codes.php).

Now we need to provide translations for each of the strings in our program in German. We can do this by marking all the strings in our program that we need translated and for which we have provided proper translations. The standard accepted way to do this is to surround your strings with `_()`. Don't worry if this seems arcane, refer to the example below.

{% highlight python linenos %}
import gettext

_ = gettext.gettext

def main():
    print(_("Hello World!"))
    print(_("Localization is fun!"))

if '__main__' == __name__:
    main()
{% endhighlight %}

Since functions in Python are first-class objects, we can move them or pass them around or even assign them to variables. This is what we're doing here. We're assigning the `gettext` function of the `gettext` module to `_` which we call later in our programs while passing our strings as arguments. You can think of this as writing `print(gettext.gettext("Hello World"))`. Nifty, right?    

Now that we've marked the strings we will provide translations for, let's provide actual translations for them.

# pygettext
We'll create a template with all of the strings which we've marked in our program so that it's easier for us to write the translations for the strings. This template is a POT with a `.pot` extension which stands for portable object template. To generate the template for our program, we can use the `pygettext.py` module which also comes bundled with the standard installation of python.

```shell
$ $(locate pygettext) -o locales/template.pot hello_world.py
```

This will generate our template file `template.pot` in the locales directory. If you view the contents of this file, you'll see metadata about the file and at the end, we can see our two strings which we had wrapped using the `gettext` function.

```text
# SOME DESCRIPTIVE TITLE.
# Copyright (C) YEAR ORGANIZATION
# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.
#
msgid ""
msgstr ""
"Project-Id-Version: PACKAGE VERSION\n"
"POT-Creation-Date: 2018-09-09 09:23+0530\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\n"
"Language-Team: LANGUAGE <LL@li.org>\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Generated-By: pygettext.py 1.5\n"


#: hello_locales:13
msgid "Hello World"
msgstr ""

#: hello_locales:14
msgid "Localization if fun!"
msgstr ""
```

Here, `msgid` denotes the original string and `msgstr` contains the translated string. Note that it also provides some info about the string, namely the filename and the line number. Next, we can just copy this file to `locales/de/LC_MESSAGES` and provide the appropriate translations. It should look like this minus the metadata.

```text
#: hello_locales:13
msgid "Hello World"
msgstr "Halo Welt"

#: hello_locales:14
msgid "Localization if fun!"
msgstr "Lokalisierung macht Spaß"
```

For the english translation (`en/`), we can make do by simply copying `template.pot` to `locales/en/LC_MESSAGES`. We can think of this template as a global template we can use for every locale or language we wish to provide a translation for, all that's required is to copy this template to the proper directory as shown in the directory convention above. 

# msgfmt
There's one more step to this before we fire up das program. `gettext` module cannot directly use the `.po` files and hence we are required to convert these files to their equivalent `.mo` files. These `.mo` files are binary machine-object files that are parsed by `gettext`. We can use the `msgfmt` tool to generate these, which also comes with the standard python installation.

```shell
$ $(locate msgfmt) locales/de/LC_MESSAGES/template.po
$ $(locate msgfmt) locales/en/LC_MESSAGES/template.po
```

This would create an equivalent `.mo` file to be used by the `gettext` module. At this point of time, our `locales` directory should look like this.

```text
locales
└── en
    └── LC_MESSAGES
        ├── template.mo
        └── template.po
└── de
    └── LC_MESSAGES
        ├── template.mo
        └── template.po
```

# Putting it together
Let's modify our program to use the appropriate translations or more aptly, to use the `.mo` files we have generated.

{% highlight python linenos %}
import gettext
import os

LOCALE = os.getenv('LANG', 'en')

_ = gettext.translation(
        'template', localedir='locales', languages=[LOCALE]).gettext


def main():
    print(_("Hello World"))
    print(_("Localization if fun!"))


if '__main__' == __name__:
    main()
{% endhighlight %}

Here we invoke the gettext.translation function which returns a `Translation` instance on which we call the `gettext` function and assign it to `_`. We pass the name of our template file as a string, also called the `domain`. Then we specify the directory which has all our translations for different locales, `locales`. Next, we provide a list of lanugages(language codes) that we wish to be parsed by `gettext`. Finally, we have used an environment variable to easily switch locales from the command line. 

We can now test our program.

```shell
$ python hello_world.py
Hello World
Localization is fun!

$ LANG=de python hello_world.py
Halo Welt
Lokalisierung macht Spaß
```

It works as expected for both english and german locales, look at how we've used the environment variable to switch to German(de) locale.

---

# Conclusion
In this post, we've seen how to localize our application. We learned how to use the `gettext` module and a bit about portable objects and portable object templates. We also used environment variables to switch locales of our application.

If there's something you'd like to improve in this article or if you've found something that's not correctly stated, feel free to contact me.

---

