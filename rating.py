# -*- coding: utf-8 -*-
# 

import os
import xbmc,xbmcaddon,xbmcgui
from utilities import *
import trakt_cache
  
__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

# read settings
__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

apikey = '0a698a20b222d0b8637298f6920bf03a'
username = __settings__.getSetting("username")
pwd = sha1(__settings__.getSetting("password")).hexdigest()
debug = __settings__.getSetting( "debug" )

headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}

def ratingCheck(curVideo, watchedTime, totalTime, playlistLength):
    __settings__ = xbmcaddon.Addon( "script.TraktUtilities" ) #read settings again, encase they have changed
    # you can disable rating in options
    rateMovieOption = __settings__.getSetting("rate_movie")
    rateEpisodeOption = __settings__.getSetting("rate_episode")
    rateEachInPlaylistOption = __settings__.getSetting("rate_each_playlist_item")
    rateMinViewTimeOption = __settings__.getSetting("rate_min_view_time")

    if (watchedTime/totalTime)*100>=float(rateMinViewTimeOption):
        if (playlistLength <= 1) or (rateEachInPlaylistOption == 'true'):
            if curVideo['type'] == 'movie' and rateMovieOption == 'true':
                doRateMovie(trakt_cache.getMovie(localId = curVideo['id']))
            if curVideo['type'] == 'episode' and rateEpisodeOption == 'true':
                doRateEpisode(trakt_cache.getEpisode(localId = curVideo['id']))

# ask user if they like the movie
def doRateMovie(movie):
    # display rate dialog
    import windows
    ui = windows.RateMovieDialog("rate.xml", __settings__.getAddonInfo('path'), "Default")
    ui.initDialog(movie)
    ui.doModal()
    del ui

# ask user if they like the show
def doRateShow(show):
    # display rate dialog
    import windows
    ui = windows.RateShowDialog("rate.xml", __settings__.getAddonInfo('path'), "Default")
    ui.initDialog(show)
    ui.doModal()
    del ui
    
# ask user if they like the episode
def doRateEpisode(episode):
    # display rate dialog
    import windows
    ui = windows.RateEpisodeDialog("rate.xml", __settings__.getAddonInfo('path'), "Default")
    ui.initDialog(episode)
    ui.doModal()
    del ui
