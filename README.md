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
album [album name]
artist [artist name]
history
image (display image in terminal - requires w3m & rxvt)
nowplaying
pause
queue
quit
random
remove
search [query]
skip
topartists
topsongs
volume [1-100]
```

Invoke `python beats_cli.py` to use the REPL, or `python beats_cli.py <command>` for a single command.
