---
layout: post
title: Go Practices
---

In this post, I'll talk about some of the practices and tips that I've learned and picked up from the interwebs and from the resources I've been referring to while learning Go.

# Introduction
I've been working with Go for the past one year or so and have been enjoying writing it, even more so than I did writing Python. Every language comes with some [quirks](https://blog.sbstp.ca/go-quirks/) and Go isn't any different. There are a number of articles on the internet that talk about specific features of Go, the best practices and what not. And over the past few months, I've been trying to keep track of these so called "best practices" that I try to enforce on myself when I write Go.

In this post, I'll talk about some of the practices and tips that I've learned and picked up from the interwebs and from the resources I've been referring to while learning Go.

# fmt.Printf
If you want to reuse arguments to a `fmt.[S]Printf` call more than once, you can avoid rewriting it and use this nifty little trick:

{% highlight go linenos %}
name := "danish"

// instead of doing this
fmt.Printf("once: %s, twice: %s, thrice: %s", name, name, name)

// you can do this
fmt.Printf("once: %s, twice: %[1]s, thrice: %[1]s", name)
{% endhighlight %}

I personally haven't used this but it's a nice-to-have piece of knowledge for one of those times.

# Initializing arrays
While initializing an empty array, you can specify a specific index to be of a certain value:

{% highlight go linenos %}
// this defines an array with 100 elements except for the last one which has value 1
nums := [...]int{99: 1}

// since months are numbered from 1, we can explicitly set the index while creating the array
// this way, months[0] would be "January" and months[0] would be "" (zero value)
months := [...]string{
    1: "January",
    2: "February",
    3: "March",
    /* ... */,
    12: "December"}
{% endhighlight %}

In line 6, we define an array of strings but since months are indexed 1, we explicitly specify the indices. The 0th index would automatically be assigned the zero value, an empty string in this case.

# Slices
Slices are interesting in terms of how they are implemented in Go. At the same time, they come with some nuances that you might find interesting and even amusing:

{% highlight go linenos %}
// since months are numbered from 1, we can explicitly set the index while creating the array
// this way, months[0] would be "January" and months[0] would be "" (zero value)
months := [...]string{1: "January", 2: "February", 3: "March", /* ... */, 12: "December"}

// start: 6; len: 3; cap: 7
summer := months[6:9] // ["June", "July", "August"]

// start: 4; len: 3; cap: 9
quarter_2 := months[4:7] // ["April", "May", "June"]
{% endhighlight %}
In line 3, we initialize an array of strings using the technique we talked about earlier in this post. Anyway, the point here is that you can create slices off of an existing array and it will act as the underlying array for the slices thus created. In line 6, the slice refers to the summer months by slicing the array `months`. To note here however is the fact that the capacity for this slice is `len(underlying-array) - starting_index`.

1. Multiple slices can refer to the same underlying array.
2. When you slice an array, it creates a new slice (concrete type).
3. The `cap` is the the the number of elements from the start of the slice to the end of the underlying array.

# Use defer (not always)
Using `defer` is muscle memory for Go programmers because it seems intuitive and results in lesser lines of code in a longer program but it's not always the right choice. Specifically, when you defer a file/resource close, your are putting yourself for potential problems. You should almost always try to explicitly close the resource and check, and return if required, any errors. Consider the snippet below:

{% highlight go linenos %}
m, err = io.Copy(f, resp.Body)

// Close file, but prefer error from Copy, if any
if closeErr := f.Close(); err == nil {
    err = closeErr
}
return n, err
{% endhighlight %}

To understand this problem, you need to understand that your operating system buffers bytes that are to be written on disk because writes to disks are very slow. It is very common that when you close the file/resource, it is only then that the operating system decides that the the contents that have been bufferred needs to be flushed to the disk and it is this error that we are categorically ignoring when we are deferring the file close.

In cases where you really have to use `defer`, probably because the way the procedure is written, consider using an inline deferred function instead of a deferred statement, like so:

{% highlight go linenos %}
m, err = io.Copy(f, resp.Body)
defer func() {
    if closeErr := f.Close(); err == nil {
        err = closeErr
    }
}()
return n, err
{% endhighlight %}

This will save quite a lot of time for you in case some IO operations didn't go as planned. To add to the same scheme, you can even log an error/warning depending on the requirements.

There's a really good [blog](https://www.joeshaw.org/dont-defer-close-on-writable-files/) written on this by Joe Shaw that you should check out to understand more about why this could be problematic for your application.


# WriteString
When writing to a type which implements a writer interface, we should use `WriteString()` instead of doing a `Write([]byte(str))` because the latter involves creating a temporary copy in memory while the former does not.

A good abstraction could be achieved this way

# Embedded structs
A good abstraction could be achieved this way and Embedding logger instance

# Naked returns
A good abstraction could be achieved this way

# Propogate formatted errors up the stack
A good abstraction could be achieved this way

# Logging structs
A good abstraction could be achieved this way

# Sorting struct elements
A good abstraction could be achieved this way
