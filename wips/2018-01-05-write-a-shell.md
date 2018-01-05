---
layout: post
title: Write a shell in C
---

I had a deep interest in Linux and when I got an opportunity to develop a shell, I was really excited. Over the course of the next month, I delved into reading about different shells in different languages, with different feature sets, aimed at different users. I finally wrote a shell in C with some basic but crucial functionalities such as piping, history etc.

# Shell  
What is a shell? In a very simple way, it could be defined as a tool or a program through which you can(should) interact with the operating system. This definition is very vague but it gives the idea.

# Requirements
- C programming knowledge
- gcc
- text editor

# Starting of the shell
This is the driving function of the loop. Let us see how things are implemented and how they work when the shell starts.
First things first, a prompt lets the user know that the terminal is ready to accept commands from the user. A prompt can be heavily customized but for the sake of simplicity, we'll set our prompt as a very basic yet popular `>` symbol. Consider the code below.

```c
void loop() {
   char * line;
   char * * args;
   int status = 1;

   do {
      printf("> ");
      line = read_line();
      flag = 0;
      args = split_lines(line);
      status = dash_launch(args);
      free(line);
      free(args);
   } while (status);
}
```

Now, let's actually focus on the more important parts. We declare a char pointer and 2d char pointer, `line` and `args` respectively. The `line` char pointer will hold the command(string) entered by the user using the `read_line()` function which is explained below. The `status` variable stores the return value of functions invoked during command execution. It will determine the termination of the loop i.e If the user enters the `exit` command, the `exit` function will return `0` which will force the control to break out of the loop and the shell would terminate. The last two lines of the do-while loop basically frees the memory used by the two pointer variables using the `free()` function, freeing up memory explicitly is required in C and is a good practice.


# Reading user commands

```c
char * read_line() {
  int buffsize = 1024;
  int position = 0;
  char * buffer = malloc(sizeof(char) * buffsize);
  int c;

  if (!buffer) {
    fprintf(stderr, "%sdash: Allocation error%s\n", RED, RESET);
    exit(EXIT_FAILURE);
  }

  while (1) {
    c = getchar();
    if (c == EOF || c == '\n') {
      //printf("\n"); 
      buffer[position] = '\0';
      return buffer;
    } else {
      buffer[position] = c;
    }
    position++;

    if (position >= buffsize) {
      buffsize += 1024;
      buffer = realloc(buffer, buffsize);

      if (!buffer) {
        fprintf(stderr, "dash: Allocation error\n");
        exit(EXIT_FAILURE);
      }
    }
  }
}
```

Let's see what's happening here, first of all, we declare an int variable, `buffsize`, and initialized it to `1024` bytes. Next, a char pointer, `buffer` variable is allocated memory through malloc the size of `buffsize`. 

The reason for using dynamic alloacation here instead of static is because you cannot determine the lenght of the command entered by the user. So, the most logical way is to allocate more memory as and when required.

An infinite while loop is started off, first line of the loop gets the character entered by the user and stores it in `c`. If it is and `EOF` or `\n`, a null terminator is returned. If not, the character is stored in hte `buffer` char pointer.

In the final conditional statement, we check if the size of `buffer` is equal to or greater than that of `bufsize` i.e if the current size of the `buffer` char pointer is equal to or greater than the size we initialized it with, we need to allocate more memory `buffer` so as to continue reading user input. For this, we double the value of `buffsize` and then pass it onto the `realloc()` function along with `buffer`. The realloc returns a variable with the new size passed as argument and all the data copied to the new variable. 

The `if(!buffer)` checks are for making sure memory was allocated to `buffer` successfully otherwise `malloc` and `realloc` return `NULL` in unsuccessfull memory allocation attempts. If that happens, our function returns with an error.

# Executing commands


