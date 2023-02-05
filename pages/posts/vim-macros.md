---
layout: post
date: 2019-02-16
title: Vim macros and the magic of recursion
---
The other day, a friend of mine asked me for a list of Indian states and their capitals in JSON format. We looked around the internet but couldn't find one which gave us the list in a format we could readily make use of. Finally, he copied a list from [this](http://adaniel.tripod.com/statelist.htm) page which was rendered as an HTML table and upon copying, it messed up. I quickly copied this list to a Vim buffer to try something out. 

# Vim macros
Macros in Vim are defined as recordings of commands which you can save to a particular register and replay later on. You can also think of them as functions in a way because they offer you to avoid doing repeatable tasks. Coming back to the list of states, it looked something like this:

```
Andhra Pradesh
	

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

- `qq`: start recording the macro into register `q`
- `0`: move cursor to first char
- `4J`: join the 3 lines below the current one
- `hi:Esc`: move cursor one position left and insert colon
- `I"Esc`: insert quote before the first char on line
- `t:a"Esc`: insert quote before the colon char
- `wi"Esc`: insert quote on the beg of the next word
- `A",Esc`: insert quote and a comma to the end of line
- `jdd`: delete the next empty line and put the cursor on the next non-empty line

That might seem like a lot but it really is just a sequence of easy to understand Vim commands. You can hit `q` again to stop recording the macro. When you are done recording, you would have ended up on a new line, a new state. You can hit `@q` to replay the commands stored in the `q` register. It will instantly repeat the commands we just tried out. `@@` is a shortcut to run previously run macro.

# Recursive Vim macros
Now, you don't want to go about hitting `@q` or `@@` 26 times. You can make use of recursive Vim macros to get away with repetitive tasks which involve macros. We will make a small addition to the list of commands that we ran previously. All we need to do is to repeat the macro when we are on a new line and as already discussed previously, we can use `@<register>` to replay the macro stored in <register>. So, our new set of commands would be 

- `qq`: start recording the macro into register `q`
- `0`: move cursor to first char
- `4J`: join the 3 lines below the current one
- `hi:Esc`: move cursor one position left and insert colon
- `I"Esc`: insert quote before the first char on line
- `t:a"Esc`: insert quote before the colon char
- `wi"Esc`: insert quote on the beg of the next word
- `A",Esc`: insert quote and a comma to the end of line
- `jdd`: delete the next empty line and put the cursor on the next non-empty line
- `@q`: To replay this macro at the beginning of a new line assuming the fact that we have used `q` to save our macro.

Once you enter this somewhat arcane list of normal commands while being on the first non-empty line of the buffer, you will see that Vim "magically" arranges everything for you and now you have this almost JSON-like file which you can read using Python and whatnot. I said almost JSON-like because it is missing the opening and closing parenthesis at the end and beginning of the file which you can just go ahead and put in manually. Your buffer should now look something like this:


```
{
    "Andra Pradesh": "Hyderabad, Amaravati",
    "Arunachal Pradesh": "Itangar",
    "Assam": "Dispur",
    "Bihar": "Patna",
    "Chhattisgarh": "Raipur",
    "Goa": "Panaji",
    "Gujarat": "Gandhinagar",
    "Haryana": "Chandigarh",
    "Himachal Pradesh": "Shimla",
    "Jammu and Kashmir": "Srinagar and Jammu",
    "Jharkhand": "Ranchi",
    "Karnataka": "Bangalore",
    "Kerala": "Thiruvananthapuram",
    "Madya Pradesh": "Bhopal",
    "Maharashtra": "Mumbai",
    "Manipur": "Imphal",
    "Meghalaya": "Shillong",
    "Mizoram": "Aizawi",
    "Nagaland": "Kohima",
    "Orissa": "Bhubaneshwar",
    "Punjab": "Chandigarh",
    "Rajasthan": "Jaipur",
    "Sikkim": "Gangtok",
    "Tamil Nadu": "Chennai",
    "Telagana": "Hyderabad",
    "Tripura": "Agartala",
    "Uttaranchal": "Dehradun",
    "Uttar Pradesh": "Lucknow",
    "West Bengal": "Kolkata",
}
```
<br>

# Other uses
This might have been trivial for some of you reading but if you think about the underlying idea this article proposes, you can put Vim macros to a variety of uses. I've used Vim macros often times, in fact whenever I see myself repeating normal mode commands, I try to do the same using recursive macros. Some of my recent uses involving Vim macros are:

- Transform all the keys in a Go map from uppercase to lowercase
- Remove multiple values from a Python dict and adding a new one
- Add a newline to lines in a file which matches a certain pattern

It's fun to solve problems in a unique way, albeit somewhat time consuming initially. They tend to pay off at the end in a sense that you get to learn a skill which comes in handy for times to come. Vim macros are a powerful way to level up your editing game. Learn more about macros in Vim using `:h macro`.

---
