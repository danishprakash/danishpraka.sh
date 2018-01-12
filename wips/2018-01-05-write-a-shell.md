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

# Tokenizing Input
Once we have the command entered by the user as a char pointer array. We'd tokenize (read split) it making it easier for us to execute them. We define the function `split_lin()` with one a character pointer as an argument. In this function, we'll do memory mangement in the same way we did it in the `read_line()` function. Other variables here include `**tokens` and `*token`. We will be using the `strtok()` function for the task. It takes two arguments, the string to be tokenized and the delimiters. 

For instance, consider this:

```
str1 = strtok("this is it!", " ");
// str1 -> "this"

str1 = strtok(NULL, " ");
//str1 = "is"

str1 = strtok(NULL, " ");
//str1 = "it!"
```

First call to the `strtok` function returns the first token and every subsequent call expects the input as `NULL` and starts from where it left off in the previous iteration. Now, the code for `split_line` should be easily understood.

```C
char * * split_line(char * line) {
  int buffsize = TK_BUFF_SIZE, position = 0;
  char * * tokens = malloc(buffsize * sizeof(char * ));
  char * token;

  if (!tokens) {
    fprintf(stderr, "%sdash: Allocation error%s\n", RED, RESET);
    exit(EXIT_FAILURE);
  }
  token = strtok(line, TOK_DELIM);
  while (token != NULL) {
    tokens[position] = token;
    position++;

    if (position >= buffsize) {
      buffsize += TK_BUFF_SIZE;
      tokens = realloc(tokens, buffsize * sizeof(char * ));

      if (!tokens) {
        fprintf(stderr, "%sdash: Allocation error%s\n", RED, RESET);
        exit(EXIT_FAILURE);
      }
    }

    token = strtok(NULL, TOK_DELIM);
  }

  tokens[position] = NULL;

  return tokens;
}
```

After every iteration, we update the `tokens` variable by assigining the `token` in it's respective `position`. And finally return the `tokens` variable.

# Exiting the shell
Since it is a simple program, a simple `return 0` statement would be enough for us to exit the program successfully. Let's create a trivial function which returns 0.


```c
int dash_exit(char **args)
{
	return 0;
}
```

We'll later on check if the user has entered `exit` and invoke this function appropriately.

# Executing commands

After all the hard work above, the last step is rather trivial, thanks to the syscalls `execvp` `fork`.

```c
int dash_execute(char * * args) {
  pid_t cpid;
  int status;
  
  if (strcmp(args[0], "exit") == 0)
  {
  	return dash_exit();
  }
  
  cpid = fork();

  if (cpid == 0) {
    if (execvp(args[0], args) < 0)
      printf("dash: command not found: %s\n", args[0]);
    exit(EXIT_FAILURE);

  } else if (cpid < 0)
    printf(RED "Error forking"
      RESET "\n");
  else {
    waitpid(cpid, & status, WUNTRACED);
  }
  
  return 1;
}
```

`fork` allows us to create a new process by duplicating the current process, referring it to as the child process. The current process is thereby referred to as the parent process. The child process is a duplicate of the current(parent) process except for the process ID. When we invoke the `fork` system call, it returns the process ID of the child in the parent process. In the child process, the process ID is `0`. So, after invoking the `fork` call, we check the value returned by it to make sure we are in the child process or the `fork` syscall executed successfully. 

If the fork was successfull, we will use the `execvp` command to execute the command. This plays out well for us because the way `execvp` works is, it replaces the current process with a new process image which in this case is the 
command that needs to be executed. It returns `-1` only if there is an error. Lastly, with the `waitpid` function, we are making sure the child process finishes successfully.

Note here that we are doing a check for the `exit` command. It doesn't matter if the `**args` variable has more items than just the string `exit`. It'll simply return the function `dash_exit` which in turn will return `0`. We could've had returned 0 right inside the check but this makes it much more understandable and makes for a good practice.

# Code

```c
#
include < stdio.h > #include < string.h > #include < stdlib.h >

  #define RL_BUFF_SIZE 1024# define TK_BUFF_SIZE 64# define TOK_DELIM " \t\r\n\a"

#
define RED "\033[0;31m"#
define RESET "\e[0m"

int dash_exit(char * * );
char * * split_line(char * );
char * read_line();
int dash_execute(char * * );

int dash_execute(char * * args) {
  pid_t cpid;
  int status;

  if (strcmp(args[0], "exit") == 0) {
    return dash_exit(args);
  }

  cpid = fork();

  if (cpid == 0) {
    if (execvp(args[0], args) < 0)
      printf("dash: command not found: %s\n", args[0]);
    exit(EXIT_FAILURE);

  } else if (cpid < 0)
    printf(RED "Error forking"
      RESET "\n");
  else {
    waitpid(cpid, & status, WUNTRACED);
  }

  return 1;
}

int dash_exit(char * * args) {
  return 0;
}

char * * split_line(char * line) {
  int buffsize = TK_BUFF_SIZE, position = 0;
  char * * tokens = malloc(buffsize * sizeof(char * ));
  char * token;

  if (!tokens) {
    fprintf(stderr, "%sdash: Allocation error%s\n", RED, RESET);
    exit(EXIT_FAILURE);
  }
  token = strtok(line, TOK_DELIM);
  while (token != NULL) {
    tokens[position] = token;
    position++;

    if (position >= buffsize) {
      buffsize += TK_BUFF_SIZE;
      tokens = realloc(tokens, buffsize * sizeof(char * ));

      if (!tokens) {
        fprintf(stderr, "%sdash: Allocation error%s\n", RED, RESET);
        exit(EXIT_FAILURE);
      }
    }

    token = strtok(NULL, TOK_DELIM);
  }

  tokens[position] = NULL;

  return tokens;
}

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

void loop() {
  char * line;
  char * * args;
  int status = 1;

  do {
    printf("> ");
    line = read_line();
    args = split_line(line);
    status = dash_execute(args);
    free(line);
    free(args);
  } while (status);
}

int main() {
  loop();
  return 0;
}
```

___

# Finishing notes
This post was more inclined towards a learning outcome rather than a full-fledged product. You'd probably never want to use a shell this basic but you probably now know how your favorite shells are working under the hood. 

I've written a more advanced version of this shell including piping, history and other inbuilt commands [here](https://github.com/prakashdanish/dash).

