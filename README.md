# beats_cli
Command line REPL for Beats

# Installation
The following dependencies are needed:
* prompt-toolkit
* pygments
* termcolor
* prettytable
* wget
* w3m (for terminal image viewing)

# Available Commands
```
add [query/url] (add song if only one search result, or stream url)
album [album name]
artist [artist name]
history
image (display album art in terminal - requires w3m & rxvt)
nowplaying
pause
queue
quit
random
remove <index>
search [query]
skip
topartists
topsongs
volume [1-100]
```

Invoke `python beats_cli.py` to use the REPL, or `python beats_cli.py <command>` for a single command.
