# -*- coding: utf-8 -*-
# 

import time
global t
t = time.time()
def tstampd(string):
    global t
    print string + " ["+str(time.time()-t)+"]"
    t = time.time()
tstampd("Start Util")

import os, sys
import xbmc,xbmcaddon,xbmcgui
import time, socket

tstampd("OS Imports")

try: import simplejson as json
except ImportError: import json
tstampd("import json")

from async_tools import *
tstampd("from async_tools import *")

from exc_types import *
tstampd("from exc_types import *")

import urllib, re

tstampd("import urllib, re")

try:
    # Python 2.6 +
    from hashlib import sha1 as sha
    sha_new = sha
except ImportError:
    # Python 2.5 and earlier
    import sha
    sha_new = sha1
  
def sha1(*args, **kwargs):
    return sha_new(*args, **kwargs)

tstampd("Import sha")
  
__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

# read settings
__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

apikey = '48dfcb4813134da82152984e8c4f329bc8b8b46a'
username = __settings__.getSetting("username")
pwd = sha1(__settings__.getSetting("password")).hexdigest()
debug = __settings__.getSetting( "debug" )

headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}

tstampd("Settings")

def Debug(msg, force=False):
    if (debug == 'true' or force):
        try:
            print "Trakt Utilities: " + unicode(msg)
        except UnicodeEncodeError:
            print "Trakt Utilities: " + msg.encode( "utf-8", "ignore" )

def notification( header, message, time=5000, icon=__settings__.getAddonInfo( "icon" ) ):
    xbmc.executebuiltin( "XBMC.Notification(%s,%s,%i,%s)" % ( header, message, time, icon ) )


global tuThreads
try:
    print tuThreads
    raise Exception("Error: tuThreads already exists")
except:
    pass  
tuThreads = Pool(10)
Pool.setGlobalPool(tuThreads)
def checkSettings(daemon=False):
    from trakt import Trakt
    if username == "":
        if daemon:
            notification("Trakt Utilities", __language__(1106).encode( "utf-8", "ignore" )) # please enter your Username and Password in settings
        else:
            xbmcgui.Dialog().ok("Trakt Utilities", __language__(1106).encode( "utf-8", "ignore" )) # please enter your Username and Password in settings
            __settings__.openSettings()
        return False
    elif __settings__.getSetting("password") == "":
        if daemon:
            notification("Trakt Utilities", __language__(1107).encode( "utf-8", "ignore" )) # please enter your Password in settings
        else:
            xbmcgui.Dialog().ok("Trakt Utilities", __language__(1107).encode( "utf-8", "ignore" )) # please enter your Password in settings
            __settings__.openSettings()
        return False
    
    try:
        data = Trakt.jsonRequest('POST', '/account/test/%%API_KEY%%', daemon=True)
    except TraktRequestFailed, e:
        Debug("Unable to rerify trakt details, continuing anyway: "+str(e))
    else:
        if data == None: #Incorrect trakt login details
            if daemon:
                notification("Trakt Utilities", __language__(1110).encode( "utf-8", "ignore" )) # please enter your Password in settings
            else:
                xbmcgui.Dialog().ok("Trakt Utilities", __language__(1110).encode( "utf-8", "ignore" )) # please enter your Password in settings
                __settings__.openSettings()
            return False
    return True

# SQL string quote escaper
def xcp(s):
    return re.sub('''(['])''', r"''", unicode(s))

# make a httpapi based XBMC db query (get data)
def xbmcHttpapiQuery(query):
    #Debug("[httpapi-sql] query: "+query)
    
    xml_data = xbmc.executehttpapi( "QueryVideoDatabase(%s)" % urllib.quote_plus(query), )
    match = re.findall( "<field>((?:[^<]|<(?!/))*)</field>", xml_data,)
    
    #Debug("[httpapi-sql] responce: "+xml_data)
    #Debug("[httpapi-sql] matches: "+str(match))
    
    return match

# execute a httpapi based XBMC db query (set data)
def xbmcHttpapiExec(query):
    xml_data = xbmc.executehttpapi( "ExecVideoDatabase(%s)" % urllib.quote_plus(query), )
    return xml_data
    
# search movies on trakt
def searchTraktForMovie(title, year=None):
    from trakt import Trakt
    query = urllib.quote_plus(title.encode('ascii', 'replace'))
    data = Trakt.searchMovies(query)
    if data is None:
        return None
    if year is not None:
        for item in data:
            if 'year' in item and item['year'] == year:
                return item
        
    options = ["Skip"]
    for item in data:
        options.append(unicode(item['title'])+" ["+unicode(item['year'])+"]")
    
    if len(data) == 0:
        return None
    
    if not xbmcgui.Dialog().yesno("Trakt Utilities", "Trakt Utilities is having trouble identifing a movie, do you want to manually choose from a list?"):
        return None
        
    while True:
        select = xbmcgui.Dialog().select("Which is correct - "+unicode(title)+" ["+unicode(year)+"]", options)
        Debug("Select: " + str(select))
        if select == -1 or select == 0:
            Debug ("menu quit by user")
            return None
        elif (select-1) <= len(data):
            return data[select-1]

# search imdb via google
def searchGoogleForImdbId(query):
    try:
        # Python 3.0 +
        import http.client as httplib
    except ImportError:
        # Python 2.7 and earlier
        import httplib
    conn = httplib.HTTPConnection("ajax.googleapis.com")
    conn.request("GET", "/ajax/services/search/web?v=1.0&q=site:www.imdb.com+"+urllib.quote_plus(query.encode('utf-8')))
    response = conn.getresponse()
    try:
        raw = response.read()
        data = json.loads(raw)
        for result in data['responseData']['results']:
            if (result['visibleUrl'] == "www.imdb.com"):
                if (re.match("http[:]//www[.]imdb[.]com/title/", result['url'])):
                    imdbid = re.search('/(tt[0-9]{7})/', result['url']).group(1)
                    return imdbid;
    except (ValueError, TypeError):
        Debug("googleQuery: Bad JSON responce: "+raw)
        notification("Trakt Utilities", __language__(1109).encode( "utf-8", "ignore" ) + ": Bad responce from google") # Error
        return None
    return None
    
# get easy access to tvshow by tvdb_id
def traktShowListByTvdbID(data):
    trakt_tvshows = {}

    for i in range(0, len(data)):
        trakt_tvshows[data[i]['tvdb_id']] = data[i]
        
    return trakt_tvshows

# get tvshows from XBMC
def getTVShowsFromXBMC():
    raise Exception("Deprecated")
    
# get seasons for a given tvshow from XBMC
def getSeasonsFromXBMC(tvshow):
    raise Exception("Deprecated")
    
# get episodes for a given tvshow / season from XBMC
def getEpisodesFromXBMC(tvshow, season):
    raise Exception("Deprecated")

# get a single episode from xbmc given the id
def getEpisodeDetailsFromXbmc(libraryId, fields):
    raise Exception("Deprecated")

# get movies from XBMC
def getMoviesFromXBMC():
    raise Exception("Deprecated")

# get a single movie from xbmc given the id
def getMovieDetailsFromXbmc(libraryId, fields):
    raise Exception("Deprecated")

# sets the playcount of a given movie by imdbid
def setXBMCMoviePlaycount(imdb_id, playcount):
    if playcount is None:
        playcount = 0
    else:
        playcount = int(playcount)
    # httpapi till jsonrpc supports playcount update
    # c09 => IMDB ID
    matches = xbmcHttpapiQuery(
    "SELECT movie.idFile FROM movie"+
    " WHERE movie.c09='%(imdb_id)s'" % {'imdb_id':xcp(imdb_id)})
     
    if not matches:
        #add error message here
        return
    for match in matches:
        result = xbmcHttpapiExec(
        "UPDATE files"+
        " SET playcount=%(playcount)d" % {'playcount':playcount}+
        " WHERE idFile=%(idFile)s" % {'idFile':xcp(match)})
        
        Debug("xml answer: " + str(result))

# sets the playcount of a given episode by tvdb_id
def setXBMCEpisodePlaycount(tvdb_id, seasonid, episodeid, playcount):
    if playcount is None:
        playcount = 0
    else:
        playcount = int(playcount)
        
    # httpapi till jsonrpc supports playcount update
    # select tvshow by tvdb_id # c12 => TVDB ID # c00 = title
    match = xbmcHttpapiQuery(
    "SELECT tvshow.idShow, tvshow.c00 FROM tvshow"+
    " WHERE tvshow.c12='%(tvdb_id)s'" % {'tvdb_id':xcp(tvdb_id)})
    
    if match:
        Debug("TV Show: " + match[1] + " idShow: " + str(match[0]) + " season: " + str(seasonid) + " episode: " + str(episodeid))

        # select episode table by idShow
        match = xbmcHttpapiQuery(
        "SELECT tvshowlinkepisode.idEpisode FROM tvshowlinkepisode"+
        " WHERE tvshowlinkepisode.idShow=%(idShow)s" % {'idShow':xcp(match[0])})
        
        for idEpisode in match:
            # get idfile from episode table # c12 = season, c13 = episode
            match2 = xbmcHttpapiQuery(
            "SELECT episode.idFile FROM episode"+
            " WHERE episode.idEpisode=%(idEpisode)d" % {'idEpisode':int(idEpisode)}+
            " AND episode.c12='%(seasonid)s'" % {'seasonid':xcp(seasonid)}+
            " AND episode.c13='%(episodeid)s'" % {'episodeid':xcp(episodeid)})
            
            if match2:
                for idFile in match2:
                    Debug("idFile: " + str(idFile) + " setting playcount...")
                    responce = xbmcHttpapiExec(
                    "UPDATE files"+
                    " SET playcount=%(playcount)d" % {'playcount':playcount}+
                    " WHERE idFile=%(idFile)s" % {'idFile':xcp(idFile)})
                    
                    Debug("xml answer: " + str(responce))
    else:
        Debug("setXBMCEpisodePlaycount: no tv show found for tvdb id: " + str(tvdb_id))
    
# get current video being played from XBMC
def getCurrentPlayingVideoFromXBMC():
    rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'Player.GetActivePlayers','params':{}, 'id': 1})
    result = xbmc.executeJSONRPC(rpccmd)
    result = json.loads(result)
    # check for error
    try:
        error = result['error']
        Debug("[Util] getCurrentPlayingVideoFromXBMC: " + str(error))
        return None
    except KeyError:
        pass # no error
    
    try:
        for player in result['result']:
            if player['type'] == 'video':
                rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'Player.GetProperties','params':{'playerid': player['playerid'], 'properties':['playlistid', 'position']}, 'id': 1})
                result2 = xbmc.executeJSONRPC(rpccmd)
                result2 = json.loads(result2)
                # check for error
                try:
                    error = result2['error']
                    Debug("[Util] getCurrentPlayingVideoFromXBMC, Player.GetProperties: " + str(error))
                    return None
                except KeyError:
                    pass # no error
                playlistid = result2['result']['playlistid']
                position = result2['result']['position']
                
                rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'Playlist.GetItems','params':{'playlistid': playlistid}, 'id': 1})
                result2 = xbmc.executeJSONRPC(rpccmd)
                result2 = json.loads(result2)
                # check for error
                try:
                    error = result2['error']
                    Debug("[Util] getCurrentPlayingVideoFromXBMC, Playlist.GetItems: " + str(error))
                    return None
                except KeyError:
                    pass # no error
                Debug("Current playlist: "+str(result2['result']))
                
                return result2['result'][position]
        Debug("[Util] getCurrentPlayingVideoFromXBMC: No current video player")
        return None
    except KeyError:
        Debug("[Util] getCurrentPlayingVideoFromXBMC: KeyError")
        return None
        
# get the length of the current video playlist being played from XBMC
def getPlaylistLengthFromXBMCPlayer(playerid):
    if playerid == -1:
        return 1 #Default player (-1) can't be checked properly
    if playerid < 0 or playerid > 2:
        Debug("[Util] getPlaylistLengthFromXBMCPlayer, invalid playerid: "+str(playerid))
        return 0
    rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'Player.GetProperties','params':{'playerid': playerid, 'properties':['playlistid']}, 'id': 1})
    result = xbmc.executeJSONRPC(rpccmd)
    result = json.loads(result)
    # check for error
    try:
        error = result['error']
        Debug("[Util] getPlaylistLengthFromXBMCPlayer, Player.GetProperties: " + str(error))
        return 0
    except KeyError:
        pass # no error
    playlistid = result['result']['playlistid']
    
    rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'Playlist.GetProperties','params':{'playlistid': playlistid, 'properties': ['size']}, 'id': 1})
    result = xbmc.executeJSONRPC(rpccmd)
    result = json.loads(result)
    # check for error
    try:
        error = result['error']
        Debug("[Util] getPlaylistLengthFromXBMCPlayer, Playlist.GetProperties: " + str(error))
        return 0
    except KeyError:
        pass # no error
    
    return result['result']['size']

def getMovieIdFromXBMC(imdb_id, title):
    # httpapi till jsonrpc supports searching for a single movie
    # Get id of movie by movies IMDB
    Debug("Searching for movie: "+imdb_id+", "+title)
    
    match = xbmcHttpapiQuery(
    " SELECT idMovie FROM movie"+
    "  WHERE c09='%(imdb_id)s'" % {'imdb_id':imdb_id}+
    " UNION"+
    " SELECT idMovie FROM movie"+
    "  WHERE upper(c00)='%(title)s'" % {'title':xcp(title.upper())}+
    " LIMIT 1")
    
    if not match:
        Debug("getMovieIdFromXBMC: cannot find movie in database")
        return -1
        
    return match[0]

def getShowIdFromXBMC(tvdb_id, title):
    # httpapi till jsonrpc supports searching for a single show
    # Get id of show by shows tvdb id
    
    Debug("Searching for show: "+str(tvdb_id)+", "+title)
    
    match = xbmcHttpapiQuery(
    " SELECT idShow FROM tvshow"+
    "  WHERE c12='%(tvdb_id)s'" % {'tvdb_id':xcp(tvdb_id)}+
    " UNION"+
    " SELECT idShow FROM tvshow"+
    "  WHERE upper(c00)='%(title)s'" % {'title':xcp(title.upper())}+
    " LIMIT 1")
    
    if not match:
        Debug("getShowIdFromXBMC: cannot find movie in database")
        return -1
        
    return match[0]
    
def playMovieById(idMovie = None, options = None):
    if (idMovie is None and options is None): return
    if (idMovie is None):
        if len(options) == 1:
            idMovie = options[0]
        else:
            choices = []
            for item in options:
                rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'VideoLibrary.GetMovieDetails', 'params': {'movieid': item, 'properties': ['file', 'streamdetails', 'runtime']}, 'id': 1})
                result = xbmc.executeJSONRPC(rpccmd)
                result = json.loads(result)
                if result is None or 'error' in result:
                    del options[item]
                    continue
                details = result['result']['moviedetails']
                choices.append(unicode("("+str(details['runtime'])+" Minutes) "+repr(details['streamdetails']))+" - "+unicode(details['file']))
            
            if len(options) == 1:
                idMovie = options[0]
            else:
                while True:
                    select = xbmcgui.Dialog().select("Which one do you want to play ?", choices)
                    Debug("Select: " + str(select))
                    if select == -1:
                        Debug ("menu quit by user")
                        return
                    elif select <= len(choices):
                        idMovie = options[select]
                        break
        
    Debug("Play Movie requested for id: "+str(idMovie))
    if idMovie == -1:
        return # invalid movie id
    else:
        rpccmd = json.dumps({'jsonrpc': '2.0', 'method': 'Player.Open', 'params': {'item': {'movieid': int(idMovie)}}, 'id': 1})
        result = xbmc.executeJSONRPC(rpccmd)
        result = json.loads(result)
        
        # check for error
        try:
            error = result['error']
            Debug("playMovieById, Player.Open: " + str(error))
            return None
        except KeyError:
            pass # no error
            
        try:
            if result['result'] == "OK":
                if xbmc.Player().isPlayingVideo():
                    return True
            notification("Trakt Utilities", __language__(1302).encode( "utf-8", "ignore" )) # Unable to play movie
        except KeyError:
            Debug("playMovieById, VideoPlaylist.Play: KeyError")
            return None

def validRemoteId(remoteId):
    if remoteId is None or not (isinstance(remoteId, str) or isinstance(remoteId, unicode)) or len(remoteId) == 0 or remoteId[0] == '_': return False
    return True
  
tstampd("Defs")
"""
ToDo:


"""


"""
for later:
First call "Player.GetActivePlayers" to determine the currently active player (audio, video or picture).
If it is audio or video call Audio/VideoPlaylist.GetItems and read the "current" field to get the position of the
currently playling item in the playlist. The "items" field contains an array of all items in the playlist and "items[current]" is
the currently playing file. You can also tell jsonrpc which fields to return for every item in the playlist and therefore you'll have all the information you need.

"""
