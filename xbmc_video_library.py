# -*- coding: utf-8 -*-
# 

import os, sys
import xbmc,xbmcaddon,xbmcgui

try: import simplejson as json
except ImportError: import json

from utilities import Debug

__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

class JsonRpcFailed(Exception):
    def __init__(self, value=""):
        self.value = value
    def __str__(self):
        return repr(self.value)

class XbmcVideoLibrary():
    @staticmethod
    def _jsonRPC(method, params):
        rpccmd = json.dumps({'jsonrpc': '2.0', 'method': method,'params': params, 'id': 1})
        result = xbmc.executeJSONRPC(rpccmd)
        result = json.loads(result)

        # check for error
        if 'error' in result:
            raise JsonRpcFailed(str(result['error']))
        
        if 'result' in result:
            return result['result']
        else:
            raise JsonRpcFailed("No result received")

    # get tvshows from XBMC
    @staticmethod
    def getTVShows(properties = ['title', 'year', 'imdbnumber', 'playcount']):
        result =  XbmcVideoLibrary._jsonRPC('VideoLibrary.GetTVShows', {'properties': properties})

        if 'tvshows' in result:
            return result['tvshows']
        else:
            return []   
        
    # get seasons for a given tvshow from XBMC
    @staticmethod
    def getSeasons(tvshowid, properties = ['season']):
        result =  XbmcVideoLibrary._jsonRPC('VideoLibrary.GetSeasons', {'tvshowid': tvshowid, 'properties': properties})

        if 'seasons' in result:
            return result['GetSeasons']
        else:
            return []   
        
    # get episodes for a given tvshow / season from XBMC
    @staticmethod
    def getEpisodes(tvshowid, season, properties = ['title', 'playcount', 'season', 'episode', 'firstaired', 'rating']):
        result =  XbmcVideoLibrary._jsonRPC('VideoLibrary.GetEpisodes', {'tvshowid': tvshowid, 'season': season, 'properties': properties})

        if 'episodes' in result:
            return result['episodes']
        else:
            return [] 

    # get a single episode from xbmc given the id
    @staticmethod
    def getEpisodeDetails(episodeid, properties):
        result = XbmcVideoLibrary._jsonRPC('VideoLibrary.GetEpisodeDetails', {'episodeid': episodeid, 'properties': properties})

        if 'episodedetails' in result:
            return result['episodedetails']
        else:
            raise JsonRpcFailed("No episode details returned")

    # get movies from XBMC
    @staticmethod
    def getMovies(properties = ['title', 'year', 'originaltitle', 'imdbnumber', 'playcount', 'lastplayed', 'runtime']):
        result = XbmcVideoLibrary._jsonRPC('VideoLibrary.GetMovies', {'properties': properties})

        if 'movies' in result:
            return result['movies']
        else:
            return []   

    # get a single movie from xbmc given the id
    @staticmethod
    def getMovieDetailsFromXbmc(movieid, properties):
        result = XbmcVideoLibrary._jsonRPC('VideoLibrary.GetMovieDetails', {'movieid': movieid, 'properties': properties})

        if 'moviedetails' in result:
            return result['moviedetails']
        else:
            raise JsonRpcFailed("No movie details returned")