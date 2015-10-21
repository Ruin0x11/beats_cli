import requests
import subprocess
import datetime
import wget
import os
import ccso
import json
import pickle
import sys
from termcolor import colored
from prompt_toolkit.shortcuts import get_input
from prompt_toolkit.contrib.completers import WordCompleter
from pygments.style import Style
from pygments.token import Token
from prettytable import PrettyTable

SESSION_FILE = "session.pickle"
BEATS_URL = "https://www-s.acm.illinois.edu/beats/1104"
MAXLEN = 30

status = dict()
current = dict()
session = dict()

s = ccso.Network("webapps.cs.uiuc.edu", 105)

def get_login():
    global session

    if os.path.isfile(SESSION_FILE):
        with open(SESSION_FILE, 'rb') as f:
            session = pickle.load(f)
        return

    username = get_input("Username: ")
    password = get_input("Password: ", is_password=True)
    r = requests.post(BEATS_URL + "/v1/session", data={"username":username, "password":password})
    if r.status_code is not 201:
        print("couldn't log in: " + r.json()['reason'])
        get_login()
    else:
        session = dict(r.json())
        with open(SESSION_FILE, 'wb') as f:
            pickle.dump(session, f, pickle.HIGHEST_PROTOCOL)

def print_queue_now():
    r = requests.get(BEATS_URL + "/v1/queue")
    print_queue(r)

def print_queue(response):
    queue = response.json()['queue']
    x = PrettyTable(["#", "Title", "Artist", "Album", "Length", "Voted By"])
    x.border = False
    x.align["Title"] = "l"
    x.align["Artist"] = "l"
    x.align["Album"] = "l"
    x.align["Length"] = "r"
    n = 0
    for song in queue:
        n += 1
        title = colored(song['title'][:MAXLEN], "blue")
        artist = colored(song['artist'][:MAXLEN], "magenta")
        if song.get('album'):
            album = colored(song['album'][:MAXLEN], "yellow")
        else:
            album = ''
        length = int(float(song['length']))
        length = colored(datetime.timedelta(seconds=length), "red")
        voter = song['packet']['user']
        voter_name = s.query('alias=' + voter)
        if not voter_name[0]:
            voter_name = voter
        else:
            voter_name = voter_name[0]['uiucedufirstname'] + " " + voter_name[0]['uiucedulastname']
        x.add_row([n, title, artist, album, length, colored(voter_name, "cyan")])
    print(x)

def print_songs(songs):
    x = PrettyTable(["#", "Title", "Artist", "Album", "Length", "Uploader", "Plays"])
    x.border = False
    x.align["Title"] = "l"
    x.align["Artist"] = "l"
    x.align["Album"] = "l"
    x.align["Length"] = "r"
    n = 0
    for song in songs:
        n += 1
        title = colored(song['title'][:MAXLEN], "blue")
        artist = colored(song['artist'][:MAXLEN], "magenta")
        album = colored(song['album'][:MAXLEN], "yellow")
        length = int(float(song['length']))
        length = colored(datetime.timedelta(seconds=length), "red")
        playcount = int(song['play_count'])
        if playcount == 0:
            playcount = ''
        uploader = song['path'].split('/')[2]
        uploader_name = s.query('alias=' + uploader)
        if not uploader_name:
            uploader_name = uploader
        else:
            uploader_name = uploader_name[0]['uiucedufirstname'] + " " + uploader_name[0]['uiucedulastname']
        x.add_row([n, title, artist, album, length, colored(uploader_name, "cyan"), playcount])
    print(x)

def random_songs():
    r = requests.get(BEATS_URL + "/v1/songs/random")
    prompt_songs(r)

def search(query):
    r = requests.get(BEATS_URL + "/v1/songs/search", params={"q":query})
    if query.startswith("artist:"):
        prompt_albums(r)
    else:
        prompt_songs(r)
    
def remove():
    r = requests.get(BEATS_URL + "/v1/queue")
    queue = r.json()['queue']
    print_queue(r)
    query = get_input("Which song? ")

    try:
        num = int(query)
    except ValueError:
        print("not an integer")
        return
    
    if 1 <= num <= len(queue):
        song = queue[num-1]
    else:
        print("not in range")
        return

    r = requests.delete(BEATS_URL + "/v1/queue/" + str(song['id']), data={'token':session['token']})
    print("Removed " + song['artist'] + " - " + song['title'] + ".")
    print_queue(r)

def show_history():
    r = requests.get(BEATS_URL + "/v1/songs/history")
    songs = r.json()['results']
    print_songs(songs)

def show_top_songs():
    r = requests.get(BEATS_URL + "/v1/songs/top_songs")
    songs = r.json()['results']
    print_songs(songs)

def show_top_artists():
    r = requests.get(BEATS_URL + "/v1/songs/top_artists")
    artists = r.json()['results']
    x = PrettyTable(["#", "Artist", "Plays"])
    x.border = False
    x.align["Artist"] = "l"
    n = 0
    for artist in artists:
        n += 1
        x.add_row([n, colored(artist['artist'], "blue"), colored(str(artist['play_count']), "magenta")])
    print(x)

def prompt_albums(r):
    albums = r.json()['results']
    n = 0
    x = PrettyTable(["#", "Album", "Songs"])
    x.border = False
    x.align['Album'] = "l"
    x.align['Songs'] = "r"
    for album in albums:
        n += 1
        x.add_row([n, colored(album['name'], "blue"), colored(str(album['num_songs']), "magenta")])
    print("Albums of " + r.json()['query'] + ":")
    print(x)
    res = get_input("Album? ")
    if not res:
        return
    try:
        num = int(res)
    except ValueError:
        print("not an integer")
    if 1 <= num <= len(albums):
        album = albums[num-1]
    else:
        print("not in range")
        return
    search("album:" + album['name'])
    
def prompt_songs(r):
    songs = r.json()['results']
    print_songs(songs)
    res = get_input("Song? ")
    if not res:
        return
    try:
        num = int(res)
    except ValueError:
        print("not an integer")
    if 1 <= num <= r.json()['limit']:
        song = songs[num-1]
    else:
        print("not in range")
        return
    response = requests.post(BEATS_URL + "/v1/queue/add", data={'token':session['token'], 'id':str(song['id'])})
    json = response.json()
    if json.get('message'):
        get_login()
    else:
        # print("Added " + song['artist'] + " - " + song['title'])
        print_queue(response)

def pause():
    r = requests.post(BEATS_URL + "/v1/player/pause", data={'token':session['token']})
    response = r.json()
    if response.get('message'):
        get_login()
    else:
        update_status(r.json())

def play_next():
    r = requests.post(BEATS_URL + "/v1/player/play_next", data={'token':session['token']})
    response = r.json()
    if response.get('message'):
        get_login()
    else:
        update_status(r.json())

def player_set_volume(query):
    try:
        vol = int(query)
    except ValueError:
        print("not an integer")
        return

    if 0 <= vol <= 100:
        r = requests.post(BEATS_URL + "/v1/player/volume", data={'token':session['token'], 'volume':vol})
        update_status(r.json())
    else:
        print("volume must be between 0 and 100.")

def now_playing():
    global current
    r = requests.get(BEATS_URL + "/v1/now_playing")
    json = r.json()
    update_status(json['player_status'])
    current = json['media']

def print_now_playing():
    r = requests.get(BEATS_URL + "/v1/now_playing")
    song = r.json()['media']
    print("Title: " + colored(song['title'], "blue"))
    print("Artist: " + colored(song['artist'], "magenta"))
    if song.get('album'):
        print("Album: " + colored(song['album'], "yellow"))
    current_time = int(float(status['current_time'] / 1000))
    current_time = datetime.timedelta(seconds=current_time)
    duration = int(float(status['duration'] / 1000))
    duration = datetime.timedelta(seconds=duration)
    print("Duration: " + colored(str(current_time) + "/" + str(duration), "red"))

def update_status(player_status):
    global status
    status = dict(player_status)

class TestStyle(Style):
    styles = {
        Token.Toolbar: '#ffffff bg:#333333',
    }

command_completer = WordCompleter([
    "random",
    "search",
    "history",
    "queue",
    "skip",
    "pause",
    "remove",
    "volume",
    "nowplaying",
    "topsongs",
    "topartists",
    "image",
], ignore_case=True)

def run_command(text):
        tex = text.split(" ", 1)

        if len(tex) is 0:
            pass
        elif len(tex) is 1:
            command = tex[0]
            query = ''
        else:
            command = tex[0]
            query = tex[1]

        if command == "random":
            random_songs()
        elif command == "search":
            search(query)
        elif command == "artist":
            search("artist:" + query)
        elif command == "album":
            search("album:" + query)
        elif command == "history":
            show_history()
        elif command == "queue":
            print_queue_now()
        elif command == "skip":
            play_next()
        elif command == "pause":
            pause()
        elif command == "remove":
            remove()
        elif command == "volume":
            player_set_volume(query)
        elif command == "nowplaying":
            print_now_playing()
        elif command == "topsongs":
            show_top_songs()
        elif command == "topartists":
            show_top_artists()
        elif command == "image":
            if current.get('art_uri'):
                wget.download(BEATS_URL + "/" + current['art_uri'])
                path, filename = os.path.split(current['art_uri'])
                subprocess.call("imgt.sh \"" + filename + "\"", shell=True)
        elif command == "quit":
            quit()
        elif not command:
            pass
        else:
            print("invalid command.")

def main():
    def get_bottom_toolbar_tokens(cli):
        global status
        global current
        state = status['state']
        volume = status['volume']
        tb = "State: " + state + " Volume: " + str(volume)
        if status.get('media'):
            artist = current['artist']
            title = current['title']
            current_time = int(float(status['current_time'] / 1000))
            current_time = datetime.timedelta(seconds=current_time)
            duration = int(float(status['duration'] / 1000))
            duration = datetime.timedelta(seconds=duration)
            tb = tb + "  Playing: " + artist + " - " + title + " " + str(current_time) + "/" + str(duration)

        return [(Token.Toolbar, tb)]

    while True:
        text = get_input('>> ',
                      get_bottom_toolbar_tokens=get_bottom_toolbar_tokens,
                      style=TestStyle,
                      completer=command_completer)

        run_command(text)

        now_playing()

if __name__ == '__main__':


    # parser = argparse.ArgumentParser(description="Run a specific chroma animation script.")
    # parser.add_argument('animation',
    #     metavar='animation',
    #     help='One of these animations: '+string.join(os.listdir('animations/'),', '),
    #     choices=os.listdir('animations/'))
    # args = parser.parse_args()
    # animation = args.animation


    get_login()
    now_playing()
    if len(sys.argv) > 1:
        text = sys.argv[1:]
        run_command(' '.join(text))
    else:
        main()
