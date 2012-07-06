# -*- coding: utf-8 -*-
# 

import xbmc,xbmcaddon,xbmcgui
import telnetlib, time

try: import simplejson as json
except ImportError: import json

import threading
from utilities import *
from rating import *
from scrobbler import Scrobbler
from viewer import Viewer
from async_tools import *

__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

# Receives XBMC notifications and passes them off to the rating functions
class NotificationService():
    scrobbler = None

    @async
    def start(self):            
        tn = None
        try:
            while (not xbmc.abortRequested):
                try:
                    tn = telnetlib.Telnet('localhost', 9090, 10)
                except IOError as (errno, strerror):
                    #connection failed, try again soon
                    Debug("[Notification Service] Telnet too soon? ("+str(errno)+") "+strerror)
                    Debug("[Notification Service] !! Ensure you have 'Allow programs on this system to control XBMC' enabled, this setting can be found in xbmc under 'System' > 'Network' > 'Services' > 'Allow programs on this system to control XBMC'")
                    time.sleep(1)
                    continue
                
                Debug("[Notification Service] Ready and waiting");
                bCount = 0
                
                while (not xbmc.abortRequested):
                    try:
                        if bCount == 0:
                            notification = ""
                            inString = False
                        [index, match, raw] = tn.expect(["(\\\\)|(\\\")|[{\"}]"], 0.2) #note, pre-compiled regex might be faster here
                        notification += raw
                        if index == -1: # Timeout
                            safeExitPoint()
                            continue
                        if index == 0: # Found escaped quote
                            match = match.group(0)
                            if match == "\"":
                                inString = not inString
                                continue
                            if match == "{":
                                bCount += 1
                            if match == "}":
                                bCount -= 1
                        if bCount > 0:
                            continue
                        if bCount < 0:
                            bCount = 0
                    except EOFError:
                        break #go out to the other loop to restart the connection
                    
                    # Deal with the notifiaction in a sub thread so that we can handle requests more efficiently
                    self._handleNotification(notification).ignore()
                    
                    safeExitPoint()
                    # Trigger update checks for the cache
                    #trakt_cache.trigger()
                time.sleep(1)
        except AsyncCloseRequest:
            tn.close()
            Debug("[Notification Service] Closing");
            raise
        else:
            if tn is not None: tn.close()
            Debug("[Notification Service] Closing");
            raise AsyncCloseRequest('')
    
    @async
    def _handleNotification(self, notification):            
        Debug("[Notification Service] message: " + str(notification))
        
        # Parse recieved notification
        data = json.loads(notification)
        
        # Forward notification to functions
        if 'method' in data and 'params' in data and 'sender' in data['params'] and data['params']['sender'] == 'xbmc':
            if data['method'] == 'Player.OnStop':
                self.scrobbler.playbackEnded()
            elif data['method'] == 'Player.OnPlay':
                if 'data' in data['params'] and 'item' in data['params']['data'] and 'id' in data['params']['data']['item'] and 'type' in data['params']['data']['item']:
                    self.scrobbler.playbackStarted(data['params']['data'])
            elif data['method'] == 'Player.OnPause':
                self.scrobbler.playbackPaused()
            elif data['method'] in ('VideoLibrary.OnUpdate', 'VideoLibrary.OnRemove'):
                if 'data' in data['params']:
                    if 'type' in data['params']['data'] and 'id' in data['params']['data']:
                        type = data['params']['data']['type']
                        id = data['params']['data']['id']
                        if type == 'episode':
                            episode = trakt_cache.getEpisode(localId=id)
                            if episode is not None:
                                episode.refresh()
                            else:
                                trakt_cache.newLocalEpisode(localId=id)
                        elif type == 'movie':
                            movie = trakt_cache.getMovie(localId=id)
                            if movie is not None:
                                movie.refresh()
                            else:
                                trakt_cache.newLocalMovie(localId=id)
        
        if 'method' in data and 'params' in data and 'sender' in data['params'] and data['params']['sender'] == 'TraktUtilities':
            if data['method'] == 'Other.TraktUtilities.View' and 'data' in data['params']:
                if 'window' in data['params']['data']:
                    window = data['params']['data']['window']
                    if window == 'watchlistMovies':
                        Viewer.watchlistMovies()
                    elif window == 'watchlistShows':
                        Viewer.watchlistShows()
                    elif window == 'trendingMovies':
                        Viewer.trendingMovies()
                    elif window == 'trendingShows':
                        Viewer.trendingShows()
                    elif window == 'recommendedMovies':
                        Viewer.recommendedMovies()
                    elif window == 'recommendedShows':
                        Viewer.recommendedShows()
            elif data['method'] == 'Other.TraktUtilities.Sync' and 'data' in data['params']:
                if 'set' in data['params']['data']:
                    setName = data['params']['data']['set']
                    trakt_cache.refreshSet(setName)
            elif data['method'] == 'Other.TraktUtilities.Stop':
                Debug("[NotificationService] Closing down TUs backend")
                tuThreads.finishUp()
            else:
                Debug("[Notification Service] Bad request from TU")
