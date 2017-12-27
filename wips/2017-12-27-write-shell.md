---
layout: post
title: Write a shell in C
---

I had a deep interest in Linux and when I got an opportunity to develop a shell, I was really excited. Over the course of the next month, I delved into reading about different shells in different languages, with different feature sets, aimed at different users. I finally wrote a shell in C with some basic but crucial functionalities such as piping, history etc.

#### **Shell** 

What is a shell? In a very simple way, it could be defined as a tool or a program through which you can(should) interact with the operating system. This definition is very vague but it gives the idea.

#### **Requirements**

- C programming knowledge
- gcc
- text editor

#### **1: Parsing user input**

First things first, a prompt lets the user know that the terminal is ready to accept and execute commands. A prompt can be heavily customized but for the sake of learning, we'll set the prompt as a very basic `>`. Consider the code below.

```c
void loop()
{
	char *line;
	char **args;
	int status=1;

	do{
		printf("> ");
		line = read_line();	
		flag = 0;
		args = split_lines(line);
		status = dash_launch(args);
		free(line);
		free(args);
	}while(status);
}

```

We declare a char pointer and 2d char pointer, `line` and `args` respectively. The `line` char pointer will hold the command(string) entered by the user using the `read_line()` function which is explained below. The `status` variable stores the return value of functions invoked during command execution. It will determine the termination of the loop i.e If the user enters the `exit` command, the `exit` function will return `0` which will force the control to break out of the loop and the shell would terminate. The last two lines of the do-while loop basically frees the memory used by the two pointer variables using the `free()` function, freeing up memory explicitly is required in C and is a good practice.
