---
layout: post
title: Vim macros and the magic of recursion
---

The other day, a friend of mine asked me for a list of Indian states and their capitals in JSON format. We looked around the internet but couldn't find one. Finally, he copied a list from [this](http://adaniel.tripod.com/statelist.htm) page which was rendered as an HTML table and upon copying, it messed up. I quickly copied this list to a vim buffer to try something out. 

# Vim macros
Macros in vim are defined as recordings of commands which you save to a particular register. You can also think of them as functions in a way because they offer you to avoid doing repeatable tasks. Coming back to the list of states, it looked something like this:

```text
Andra Pradesh
	

Hyderabad, Amaravati

Arunachal Pradesh
	

Itangar

Assam
	

Dispur

Bihar
	

Patna

Chhattisgarh
	

Raipur
```

I've snipped the whole output of this for brevity but you get the idea. Essentially, what we have here is the name of the city, followed by two newlines and then the name of it's capital, repeated for all of the 27 states. Nevermind the mess, let's get to it.

You alread know that a macro is a sequence of commands which you can execute again and again by specifying the register to which the command is spaced. So, all I need to do is come up with a sequence and then repeat it `n` times.

Start recording the macro by hitting the `q`. For the first state, we can build a key value pair using what we have using the following sequence of commands, assuming you are on the first line of the file:

1. `0`: move cursor to first char
2. `4J`: join the 3 lines below the current one
2. `hi:Esc`: move cursor one position left and insert colon
4. `I"Esc`: insert cursor before the first char on line
5. `t:a"Esc`: insert quote before the colon char
6. `wi"Esc`: insert quote on the beg of the next word
7. `A",Esc`: insert quote and a comma to the end of line
8. `j`: move cursor to the next line

That might seem like a lot but it really is just a sequence of easy to understand vim commands. See the gif below to see these commands in action.

