from tkinter import *
from tkinter import filedialog
from tkinter import ttk
import requests
import pygame
import random
from tkinter.messagebox import showinfo
from lyrics_extractor import SongLyrics
from requests.exceptions import Timeout
import pymongo
import json
import urllib
import base64
from io import BytesIO
from PIL import ImageTk, Image
from mutagen.mp3 import MP3
import webbrowser


CLIENT_ID = 'eab56b94c3e8449794b46717080609b9'
CLIENT_SECRET = 'bd23f78d31fb4c7bbdda106db8484151'

AUTH_URL = 'https://accounts.spotify.com/api/token'


auth_response = requests.post(AUTH_URL, {
    'grant_type': 'client_credentials',
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
})


auth_response_data = auth_response.json()


access_token = auth_response_data['access_token']


headers = {
    'Authorization': 'Bearer {token}'.format(token = access_token)
}
BASE_URL = 'https://api.spotify.com/v1/search/'


loop = Tk()

myclt = pymongo.MongoClient("localhost", 27017)
mydb = myclt["music"]
col = mydb["users"]


pause_state = False
shuffle_state = [False, []]
songlen = 0
currpos = 0
stop_state = False
nexts = False
shiftit = 0

def getuser(name):
    if not name:
        showinfo("Window", "Enter name")
        name_entry.delete(0, END)
        return

    query = {"name": name}
    if not col.count_documents(query):
        showinfo("Window", "User not found")
        name_entry.delete(0, END)
        return
    details = col.find(query)
    userplaylist = []
    for i in details:
        userplaylist.extend(i['myplaylist'])
    Clearplaylist()
    for song in userplaylist:
        playground.insert(END, str(song))

def updateuser(name):
    if not name:
        showinfo("Window", "Enter name")
        name_entry.delete(0, END)
        return
    filter = {'name':name}
    if not col.count_documents(filter):
        showinfo("Window", "User not found")
        name_entry.delete(0, END)
        return
    userplaylist = list(playground.get(0, END))
    query = { "$set" : {"myplaylist": userplaylist}}
    col.update_one(filter, query)

def storeuser(name):
    if not name:
        showinfo("Window", "Enter name")
        name_entry.delete(0, END)
        return
    query = {"name": name}
    if col.count_documents(query):
        showinfo("Window", "User already exists")
        name_entry.delete(0, END)
        return
    userplaylist = list(playground.get(0, END))
    if not userplaylist:
        showinfo("Window", "Please provide atlease one song")
        name_entry.delete(0, END)
        return

    user = {"name": name, "myplaylist": userplaylist }
    x = col.insert_one(user)


#To open a given url in web browser

def callback(url):
    webbrowser.open_new(url)

def onselect(evt):

    w = evt.widget
    index = int(w.curselection()[0])
    value = w.get(index)
    e2.delete(0,END)
    e2.insert(END,value)



def addsongs():
    addedsongs = filedialog.askopenfilenames(initialdir = "/Audio", title = "Pick Song", filetypes = (("mp3 Files","*.mp3"),))
    for song in addedsongs:
        l = ((song.split('/'))[-1]).split('.')
        playground.insert(END,str(l[0]))

def calclength(song):
    songlen = int(MP3(song).info.length)
    return songlen

def duration(songlen):
    m1,s1 = divmod(songlen, 60)
    if s1 >= 10:
        lentime.config(text = f'{m1}:{s1}')
    else:
        lentime.config(text = f'{m1}:0{s1}')



def playsong():
    global pause_state
    global songlen
    global stop_state
    global currpos
    global nexts
    stop_state = False


    if(pause_state):
        pygame.mixer.music.unpause()
        pause_state = False
    else:
        song = playground.get(ACTIVE)
        playground.selection_set(ACTIVE, last = None)
        e2.delete(0, END)
        e2.insert(END, song)

        song = '/Users/arhantarora/PythonZankyo/Audio/' + song + '.mp3'
        pygame.mixer.music.load(song)
        pygame.mixer.music.play(loops = 0)
        songlen = calclength(song)
        duration(songlen)
        def timemysong():
            global currpos
            currpos2 = int(pygame.mixer.music.get_pos() / 1000)
            if(stop_state == True or currpos2 == 0 and currpos != 0):
                return

            global shiftit
            if (pause_state==False):
                currpos+=1
            shiftit = currpos / songlen * 100
            timescrub.configure(value = shiftit)
            m2,s2 = divmod(int(currpos), 60)

            postime.config(text = f'{m2}:{s2}')
            if(timescrub.get() >= 99.9 or stop_state == True):
                currpos = 0
                shiftit = 0
                stopsong()

            else:
                postime.after(1000, timemysong)
        currpos = 0
        shiftit = 0
        timemysong()



def scrub(x):
    global shiftit
    global currpos
    toset = timescrub.get() * songlen / 100
    shiftit = toset * 100
    currpos = toset
    pygame.mixer.music.set_pos(toset)

def stopsong():
    global stop_state
    pygame.mixer.music.stop()
    stop_state = True
    timescrub.configure(value=0)
    postime.config(text=f'{0}:{00}')
    lentime.config(text=f'{0}:{00}')
    playground.selection_clear(ACTIVE)
    e2.delete(0, END)
    playground.activate(0)


def pausesong(is_paused):
    global pause_state
    pause_state = is_paused
    if pause_state:
        pygame.mixer.music.unpause()
        pause_state = False

    else:
        pygame.mixer.music.pause()
        pause_state = True

def nextSong():
        next_song = (playground.curselection())[0] + 1
        x = playground.size()
        if next_song == x:
            next_song = 0
        playground.selection_clear(0,END)
        playground.activate(next_song)
        playground.selection_set(next_song, last = None)
        playsong()

def previousSong():
    pre_song = (playground.curselection())[0] - 1
    if pre_song == -1:
        pre_song = playground.size() - 1


    playground.selection_clear(0,END)
    playground.activate(pre_song)
    playground.selection_set(pre_song, last = None)
    playsong()

def randomSongs():
    l = list(range(playground.size()))
    random.shuffle(l)
    return l


def shuffle():
    global shuffle_state
    if shuffle_state[0]:
        scrubFrame.grid()
        shufbt.config(text = "Shuffle and Relax")
        for i in icon_list[:5]:
            i["state"] = "normal"
        shuffle_state[0],shuffle_state[1] = False,[]
        stopsong()

    else :
        scrubFrame.grid_forget()
        shuffle_state[0], shuffle_state[1] = True, randomSongs()
        shufbt.config(text = "Manual Mode")
        for i in icon_list[:5]:
            i["state"] = "disabled"
        playShuffle()


def playShuffle():

    if not shuffle_state[0]:
        return
    if not shuffle_state[1]:
        shuffle()
        return
    song = shuffle_state[1].pop()
    playground.selection_clear(0,END)
    playground.activate(song)
    song = playground.get(ACTIVE)
    playground.selection_set(ACTIVE, last = None)
    e2.delete(0, END)
    e2.insert(END, song)
    song = '/Users/arhantarora/PythonZankyo/Audio/' + song + '.mp3'
    pygame.mixer.music.load(song)
    pygame.mixer.music.play()
    len = calclength(song)
    if shuffle_state[0]:
        e2.after(len * 1000, playShuffle)





def popup_showinfo(message):
    showinfo("Window", message)


def printlyrics(code,arr,lyrics,song = 'NO LYRICS FOUND'):
    win = Toplevel()
    win.geometry("1500x500")
    win.wm_title('Window')
    T = Text(win)
    S = Scrollbar(win, command = T.yview)
    T.config(yscrollcommand = S.set)
    T.pack(side = LEFT)
    T.insert(END, song)

    URL = arr[0]
    response = requests.get(URL)
    im = Image.open(BytesIO(response.content))
    photo = ImageTk.PhotoImage(im)

    label = Label(win, image = photo)
    label.image = photo
    label.pack()

    Label(win, text = arr[1] ).pack()
    link2 = Label(win, text = arr[2] , fg = "blue", cursor = "hand2")
    link2.pack()
    link2.bind( "<Button-1>", lambda e: callback(lyrics[0]))
    link3 = Label(win, text = arr[3], fg = "blue", cursor = "hand2")
    link3.pack()
    link3.bind( "<Button-1>", lambda e: callback(lyrics[1]))
    Label(win, text = 'Top albums by the artist').pack()

    links = ['q'] * len(arr[4])
    for i in range(len(arr[4])):
        links[i] = Label( win, text = arr[4][i], fg = "blue", cursor = "hand2")

    for i in range(len(arr[4])):
        links[i].bind( "<Button-1>", lambda e, url= lyrics[i + 2]: webbrowser.open_new(url) )

    for i in range(len(arr[4])):
        links[i].pack() 




def getlyrics(song):

    if (not song):
        popup_showinfo('Please fill the information')
        return

    e2.delete(0, END)
    extract_lyrics = SongLyrics("AIzaSyB_2KRVPtP7AxWwTxKC4C9UecXbQTMASr4","1bf00c72a4acb9c4a")

    song = song
    spotify = requests.get(BASE_URL, params = {'q': song, 'limit': 1, 'type': 'track'}, headers = headers)
    spotify_response = spotify.json()
    itunes = 'https://itunes.apple.com/search?term=' + song + '&limit=1'
    itunes_response = requests.get(itunes).json()
    try:
        artist_image = spotify_response['tracks']['items'][0]['album']['images'][1]["url"]
    except:
        popup_showinfo('No info found')
        return

    c = 'https://itunes.apple.com/lookup?id=' + str(itunes_response['results'][0]["artistId"]) + '&entity=album'
    d = requests.get(c).json()

    links_array = []
    links_array.append(str(spotify_response['tracks']['items'][0]['album']['artists'][0]["external_urls"]['spotify'] ) )
    links_array.append(str(itunes_response['results'][0]["artistViewUrl"] ) )

    artist_name = itunes_response['results'][0]['artistName']
    a_sl = 'Top tracks on Spotify: ' + spotify_response['tracks']['items'][0]['album']['artists'][0]["external_urls"]['spotify']
    a_al = 'Top tracks on Apple Music: ' + itunes_response['results'][0]["artistViewUrl"]
    l = []
    for i in range(1, 5):
        l.append(d['results'][i]["collectionName"] + ' : ' + d['results'][i]["collectionViewUrl"] )
    arr = [artist_image, artist_name, a_sl, a_al,l]

    try:
        l = extract_lyrics.get_lyrics(song)
    except:
        popup_showinfo('No lyrics found')
        printlyrics(0, arr)
    else:

        printlyrics( 1, arr, links_array, l['lyrics'] )

def Rem1():
    playground.delete(playground.curselection()[0])
    stopsong()
    pygame.mixer.music.stop()

def Clearplaylist():
    playground.delete(0, END)
    stopsong()
    pygame.mixer.music.stop()

def changetheme(color):
    for i in button_list:
        i.config(highlightbackground = color)
    for i in icon_list:
        i.config(bg = color)



def Themesetter(scrubFrame, shufbt, imagespace, imagespace1, imagespace2, loop, masterFrame, volumeFrame, playground, playbt, pausebt, nextbt, prevbt, stopbt, postime, lentime, colscheme):
    if colscheme == "MONOCHROME":
        changetheme("#454545")

        playground.config(bg = "#000000", fg = "#ffffff", selectbackground = "#303030", selectforeground = "#ffffff")
        volumeFrame.config(fg = "#ffffff")
        postime.config(fg = "#ffffff")
        lentime.config(fg = "#ffffff")
        name.config(fg = "#ffffff")
        sn.config(fg = "#ffffff")


    elif colscheme == "Glacier":
        changetheme("#20c3d0")
        playground.config(bg = "#b9e8ea", fg = "#000000", selectbackground = "#86d6d8", selectforeground = "#000000")
        volumeFrame.config(fg = "#000000")



    elif colscheme == "Autumn Leaves":
        changetheme("#FF4E50")
        playground.config(bg = "#FFAAA6", fg = "#000000", selectbackground = "#FF4E50", selectforeground = "#ffffff")
        postime.config(fg = "#ffffff")
        lentime.config(fg = "#ffffff")
        name.config(fg = "#ffffff")
        sn.config(fg = "#ffffff")
        volumeFrame.config(fg = "#ffffff")



    elif colscheme == "Spring":
        changetheme("#A8E6CE")
        playground.config(bg = "#DCEDC2", fg = "#000000", selectbackground = "#A8E6CE", selectforeground = "#ffffff")
        postime.config(fg = "#000000")
        lentime.config(fg = "#000000")
        name.config(fg = "#000000")
        sn.config(fg = "#000000")
        volumeFrame.config(fg = "#000000")



    elif colscheme == "Summer":
        changetheme("#F3872F")
        playground.config(bg = "#ffcc99", fg = "#000000", selectbackground = "#ff944d", selectforeground = "#000000")
        volumeFrame.config(fg = "#ffffff")


def volume(x):
  pygame.mixer.music.set_volume(1 - sliderVolume.get())
  currentVolume = pygame.mixer.music.get_volume()



loop.title("Zankyo Player")
loop.iconbitmap("Graphics/ZankyoIcon2.ico")
loop.geometry("900x600")
loop.configure(bg = "#A8E6CE")

masterFrame = Frame(loop)
masterFrame.configure(bg = "#A8E6CE")
masterFrame.pack(pady = 20)

playground = Listbox(masterFrame, bg = '#DCEDC2', fg = "#000000",width = 80, bd = 5, selectbackground = "#A8E6CE", selectforeground = "#ffffff")
playground.bind('<<ListboxSelect>>', onselect)
playground.grid(row = 0, column = 0)
pygame.mixer.init()
playimg = PhotoImage(file = "Graphics/Playb.png")
pauseimg = PhotoImage(file = "Graphics/Pauseb.png")
nextimg = PhotoImage(file = "Graphics/Nextb.png")
previmg = PhotoImage(file = "Graphics/Prevb.png")
stopimg = PhotoImage(file = "Graphics/Stopb.png")

imagespace = Frame(masterFrame)
imagespace.configure(bg = "#A8E6CE")
imagespace.grid(row = 1, column = 0, pady = 20)

volumeFrame = LabelFrame(masterFrame, text = "Volume")
volumeFrame.grid(row = 0, column = 1, padx = 20)
volumeFrame.configure(bg="#A8E6CE")
playbt = Button(imagespace,image = playimg, borderwidth = 0, bg = "#A8E6CE", command = playsong)
pausebt = Button(imagespace,image = pauseimg, borderwidth = 0, bg = "#A8E6CE", command = lambda: pausesong(pause_state))
prevbt = Button(imagespace,image = previmg, borderwidth = 0, bg = "#A8E6CE", command = previousSong)
nextbt = Button(imagespace,image = nextimg, borderwidth = 0, bg = "#A8E6CE", command = nextSong)
stopbt = Button(imagespace,image = stopimg, borderwidth = 0, bg = "#A8E6CE", command = stopsong)
shufbt = Button(imagespace,text = "Shuffle and Relax", highlightbackground = "#A8E6CE", borderwidth = 0, bg = "#A8E6CE", command = shuffle)


prevbt.grid(row = 0, column = 0)
playbt.grid(row = 0, column = 1)
pausebt.grid(row = 0, column = 2)
stopbt.grid(row = 0, column = 3)
nextbt.grid(row = 0, column = 4)
shufbt.grid(row = 0, column = 5)


imagespace2 = Frame(loop)
imagespace2.configure(bg = "#A8E6CE")
imagespace2.pack(pady = 10)
name = Label(imagespace2, bg = "#A8E6CE", text = "Name:")
name.grid(row = 7, column = 0)

name_entry = Entry(imagespace2, highlightbackground = "#A8E6CE")
name_entry.grid(row = 7, column = 2)

bt = Button(imagespace2, text = "Load Playlist", highlightbackground = "#A8E6CE", command = lambda :getuser(name_entry.get()))
bt.grid(row = 10, column = 0)
bt1 = Button(imagespace2, text = "Update Playlist", highlightbackground = "#A8E6CE", command = lambda :updateuser(name_entry.get()))
bt1.grid(row = 10, column = 2)
bt2 = Button(imagespace2, text = "Store Playlist", highlightbackground = "#A8E6CE", command = lambda :storeuser(name_entry.get()))
bt2.grid(row = 10, column = 4)
imagespace1 = Frame(loop)
imagespace1.configure(bg = "#A8E6CE")
imagespace1.pack(pady = 10)


sn = Label(imagespace1, bg = "#A8E6CE", text = "Song Name:")
sn.grid(row = 4, column = 0)

e2 = Entry(imagespace1,highlightbackground = "#A8E6CE")


e2.grid(row = 4, column = 2)
b = Button(imagespace1, text = "Get Lyrics", highlightbackground = "#A8E6CE", command = lambda :getlyrics(e2.get()))
b.grid(row = 4, column = 4)

menu1 = Menu(loop)
loop.config(menu = menu1) # sort of like main menu widget
#For adding songs
dropaddmenu = Menu(menu1) #a menu we need
menu1.add_cascade(label = "Add Songs", menu = dropaddmenu) #add a cascade menu to the main widget and call it dropadd menu
dropaddmenu.config(bg = "#ffffff")
dropaddmenu.add_command(label = "Add Songs to the Playlist", command = addsongs)

dropremovemenu = Menu(menu1)
menu1.add_cascade(label = "Remove Songs", menu = dropremovemenu)
dropremovemenu.add_command(label = "Remove Song", command = Rem1)
dropremovemenu.add_command(label = "Clear Playlist", command = Clearplaylist)
dropremovemenu.config(bg = "#ffffff")

Themes = Menu(menu1)
menu1.add_cascade(label = "Themes", menu = Themes)
Themes.add_command(label = "Monochrome", command = lambda: Themesetter(scrubFrame,shufbt,imagespace,imagespace1,imagespace2,loop,masterFrame,volumeFrame,playground,playbt,pausebt,nextbt,prevbt,stopbt,postime,lentime,"MONOCHROME"))
Themes.config(bg = "#ffffff")
Themes.add_command(label = "Glacier", command = lambda: Themesetter(scrubFrame,shufbt,imagespace,imagespace1,imagespace2,loop,masterFrame,volumeFrame,playground,playbt,pausebt,nextbt,prevbt,stopbt,postime,lentime,"Glacier"))
Themes.add_command(label = "Autumn Leaves",command = lambda: Themesetter(scrubFrame,shufbt,imagespace,imagespace1,imagespace2,loop,masterFrame,volumeFrame,playground,playbt,pausebt,nextbt,prevbt,stopbt,postime,lentime,"Autumn Leaves"))
Themes.add_command(label = "Spring", command = lambda: Themesetter(scrubFrame,shufbt,imagespace,imagespace1,imagespace2,loop,masterFrame,volumeFrame,playground,playbt,pausebt,nextbt,prevbt,stopbt,postime,lentime,"Spring"))
Themes.add_command(label = "Summer", command = lambda: Themesetter(scrubFrame,shufbt,imagespace,imagespace1,imagespace2,loop,masterFrame,volumeFrame,playground,playbt,pausebt,nextbt,prevbt,stopbt,postime,lentime,"Summer"))
scrubFrame = LabelFrame(masterFrame)
scrubFrame.configure(bg = "#A8E6CE")
scrubFrame.grid(row = 2, column = 0)

sliderVolume = ttk.Scale(volumeFrame, from_ = 0, to = 1, orient = VERTICAL, value = 0, command = volume, length = 100)
sliderVolume.pack(pady = 10)
timescrub = ttk.Scale(scrubFrame, from_ = 0, to = 100, orient = HORIZONTAL, value = 0, command = scrub, length = 300)
timescrub.pack(pady = 20)
postime = Label(scrubFrame, text = "0:00", bg = "#A8E6CE")
postime.pack(after = timescrub, pady = 2)
lentime = Label(scrubFrame,text="0:00",bg="#A8E6CE")
lentime.pack(after = postime, pady = 2)
button_list = [shufbt, bt, bt1, bt2, b,name_entry,e2]
icon_list = [playbt, pausebt, prevbt, nextbt, stopbt,loop,postime,lentime,masterFrame,volumeFrame,imagespace,imagespace1,imagespace2,shufbt, scrubFrame, name, sn]

loop.mainloop()
