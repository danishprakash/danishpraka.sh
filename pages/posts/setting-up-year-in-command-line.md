---
layout: post
date: 2026-01-03
title: Setting up Year in Command Line
---

## Background

I've tracked my command line history in a MariaDB instance for the past 5 years. The original idea was to simple keep track of everything I do on the command line so that I can refer to them later on. The utility of the `history` command was immediately apparent to me and so the logical next step was to store the history in a more sophisticated setup.

I remember I looked around the internet looking for answers, and found [this](https://github.com/digitalist/bash_database_history) repository. I set up the database as per the instructions with a few changes, and then forgot about it for 2 years. Later, as the year 2022 came to a close, and inspired by the year-end reviews by various applications and services such as Spotify Wrapped, Strava Year in Review, etc, I thought about doing a similar year end review but for my command-line usage using the data I've gathered.

The [result](/posts/year-in-command-line/) was surprisingly good. It had good reception with readers, and most of all, I enjoyed the whole process of deriving insights, generating charts from the data, quite a lot. I also recently wrote a [2025](/posts/year-in-command-line-2025), and have potentially commited to a every-5-years cadence to this series.

You can checkout the analyses I've done in the past:

- [Year in Command Line (2022)](/posts/year-in-command-line)
- [Year in Command Line (2025)](/posts/year-in-command-line-2025)

I thought about adding a Methodology section to the 2025 analysis post explaining how to use the data to create a year-in-command-line based on your own data, if you decide to. But I believe a separate post would be ideal, and I can perhaps go into a little more detail. Let's get into it.

## 0. Prerequisites

The setup is quite straightforward, make sure you have the following installed:

1. `mariadb`
2. `zsh` or `bash`
3. `python` (for visualization)

## 1. Setup Database

Create a database in mariadb using the queries below. The schema consists of, among other fields, the command, current working directory, and the timestamp.

```sql
create database if not exists bash ;
use bash ;
CREATE TABLE `history` (
  `oid` bigint(20) NOT NULL AUTO_INCREMENT,
  `command` TEXT,
  `arguments` TEXT,
  `cwd` TEXT,
  `created` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `tag` TEXT,
  PRIMARY KEY (`oid`),
  KEY `created` (`created`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ;
```

## 3. Shell Integration
### The `preexec` Hook

This is a special function in zsh and is executed after a command is read and just before executing it. The idea with using this hook is to store the read command in our database and then continue on with the execution of the said command. The following snippet achieves this:


Add the following to your `.zshrc`:

```zsh
preexec() {
    BASH_COMMAND=$1
    if [[ -z "$HISTORY_TAG" ]]; then
        HISTORY_TAG=''
    else
        echo TAG: $HISTORY_TAG
    fi

    [ -n "$COMP_LINE" ] && return
    [ "$BASH_COMMAND" = "$PROMPT_COMMAND" ] && return

    local cur_cmd=$(echo $1 | sed -e "s/^[ ]*[0-9]*[ ]*//g")
    cwd=$(pwd)

    # Optional: ignore certain commands
    [[ "$BASH_COMMAND" =~ historyMysql* ]] && return
    [[ "$BASH_COMMAND" =~ _pyenv_virtualenv_hook* ]] && return

    printf -v BASH_COMMAND_ESCAPE "%q" "$BASH_COMMAND"

    mariadb -ucli-history -e "INSERT INTO sh.history (oid, command, arguments, cwd, created, tag) values (0, '${BASH_COMMAND_ESCAPE}', '', '$cwd', NOW(), '$HISTORY_TAG' )"
}
```

You can also tag certain commands if you wish to, for instance `export HISTORY_TAG=macOS` would make it easier to filter out commands that you ran on your Mac machine.

`source ~/.zshrc` and that's all you need to get started. If you're a bash user, you can use [this](https://github.com/digitalist/bash_database_history/blob/master/bashrc_trap.sh) snippet. I haven't tried bash but it should work just the same.

To test whether the setup is working, run the following command to verify:

```sh
$ mariadb -ucli-history sh -Nse "SELECT command FROM history ORDER BY created DESC LIMIT 1"
mariadb -ucli-history sh -Nse "SELECT command FROM history ORDER BY created DESC LIMIT 1"
```

The above command runs a query in the history database that we created earlier and shows the most recent command that was stored in it. Since preexec work just after parsing the command but before executing it, we should see the same `mariadb` command as the output.


## 4. Backup

Before we get to analyzing the data we will gather, it's also equally important that you keep this data safe. The most important bit here is our database dump. Keeping a regular backup--I recommend daily--of your database dump file will ensure you won't lose your terminal history. At its core, dumping your DB is as simple as:

```
$ mariadb-dump -ucli-history --skip-lock-tables sh> sh_history_dump.sql
```

You can store this dump anywhere you'd like. If you already have a backup pipeline in place using tools such as restic or rclone, you can simply plug in this command have this dump backed up regularly. If you want something simpler, you could wrap this command in a bash script, and coupled with either cron or systemd-timers, you can automate a daily dump push to any cloud service, or even a Github repo.

## Analysis & Visualization

Once you have enough data, ideally an year's worth, the next step is to analyze and visualize the data you've gathered.

For the 2022 analysis, I wrote throwaway python scripts to generate the charts. I thought about the kind of charts that would make sense, the kind of insights I could draw from those charts and any potential actionable items that would be worth talking about.

In 2025, I delegated the task of writing throwaway script to an LLM agent that are clearly suited for such tasks. I've packaged that into a simple script in a repository--[danishprakash/year-in-command-line](https://github.com/danishprakash/year-in-command-line)--that can be used as a plug-n-play script to generate a lot of charts that can get you started.

Using the script is as simple as having pythong installed, you can then:

```bash
$ git clone https://github.com/danishprakash/year-in-command-line
$ cd year-in-command-line

$ python3 -m venv venv
$ source venv/bin/activate  # On Windows: venv\Scripts\activate
$ pip install -r requirements.txt

$ python analyze.py --year 2025

$ deactivate
```

Once run, the script will create a `charts/` directory and generate all of the charts inside that directory. You can refer to the README in that repository to see the different kinds of charts that it creates, and the customization options available for it.

## Other uses

#### History recall

Apart from making for a nice end-of-year retrospective article on your command line usage, the data can be used for other things as well. One really good use-case is for history recall. Paired up with `fzf` to read the history from your MariaDB instance, you can fuzzy search across years of shell history. It's extremely efficient if you work a lot on the command line. I used the following snippet that allowed me to fuzzy search through my entire shell history for the past 5 years:

```bash
fzf-history-widget() {
selected=( $(mariadb -ucli-history -B -e "select distinct command from sh.history group by command order by max(created) desc, command;" |
    FZF_DEFAULT_OPTS="$FZF_DEFAULT_OPTS -n2..,.. --tiebreak=index --bind=ctrl-r:toggle-sort $FZF_CTRL_R_OPTS --query=${(qqq)LBUFFER} +m" fzf) )
  local ret=$?

  BUFFER="$selected"    # populate input prompt
  CURSOR=$#RBUFFER      # set cursor position at the end of the command inserted
  zle reset-prompt

  return $ret
}
zle     -N   fzf-history-widget
bindkey '^R' fzf-history-widget
```

But clearly that's not as efficient and doesn't scale as you gather more and more data. I now have a modified version where I apply a few filters and limits before fzf shows me the data.

#### Debugging

On those fateful days when you pushed something that you weren't supposed to and need to figure out the command to blame? You could search for all the commands you ran between a given time period:

```bash
SELECT command, created FROM history
WHERE created BETWEEN '2025-12-15 14:00:00' AND '2025-12-15 15:00:00'
ORDER BY created;
```

## Conclusion

The entire setup takes less than 5 minutes, but the value compounds over time:
by the end of 2026, you'll have a year's worth of data to analyze, visualize and even optimize your workflow. Or quite simply, recall that obscure command from 8 months ago.

If you end up using this for something interesting, I'd love to hear about it.

:wq
