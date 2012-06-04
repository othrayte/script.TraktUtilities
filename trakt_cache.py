# -*- coding: utf-8 -*-
# 

import xbmc,xbmcaddon
from utilities import *
from identifiable_object import IdentifiableObject
from movie import Movie
from show import Show
from episode import Episode
from ttl import TTL
from tc_queue import TCQueue
from ids import *
from datetime import timedelta, datetime
import shelve
from trakt import Trakt
from async_tools import Pool, AsyncCall, async

from exceptions import *

__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString
username = __settings__.getSetting("username")

###################
# Caches all information between the add-on and the web based trakt api
#
# trakt_cache is a group of functions that organise and maintain the cached information between xbmcs DB and the one at
# trakt.tv. It is based on the rational that you only want to keep certain peices of information up to date but that you
# might want it again soon and there is no point in going and getting it all over again.
#
# Information is stored in a DB file in the filesystem using 'shelfs'. To make these safe for using in theaded programs
# the SafeShelf class has been created, this allows multiple reads simultaniously but locks the whole db down for
# writes.
#
# Access for reading is like this:
#     with SafeShelf('movies') as movies:
#         #Do stuff with the DB
#         foo = movies['bar']
#
# Access for writing is like this:
#     with SafeShelf('movies', True) as movies:
#         #Do stuff with the DB
#         movies['foo'] = bar
#
# Internally the caching is based on sets and items, a set is a list of items, like the watchlist or the recommended
# movies list. Each set has an associated refresher function unless it is not cached (like the trending lists).
#
# When any request is make for a set or information from an item a check is performed to make sure that the information
# is as recent as it required, and if it is not the associated refresher is executed to get newer information.
#
# Internally to find the changes between the new copys of the items and the old ones a generalised comparitor is
# provided, this has a list of known variables to look for changes in.
#
# Basic operation of trakt_cache starts with:
#     trakt_cache.init("the/path/to/the/dbs/and/the/common/part/of/the/db/name")
# 
# From this point any requests for data with a function like:
#     trakt_cache.getMovieLibrary()
# or the more abstracted:
#     sets.Movies.library()
# will return information that is up to date within internally defined standards
##

_location = None
  
##
# Cache DB operations
##

def init(location=None):
    from sqlobject import sqlhub, connectionForURI
    import sys, os

    db_filename = os.path.abspath(xbmc.translatePath(location)+'.db')
    #if os.path.exists(db_filename):
    #    os.unlink(db_filename)
    connection_string = 'sqlite:' + db_filename
    connection = connectionForURI(connection_string)
    sqlhub.processConnection = connection

    if not IdentifiableObject.tableExists():
        IdentifiableObject.createTable()
    if not Movie.tableExists():
        Movie.createTable()
    if not RemoteId.tableExists():
        RemoteId.createTable()
    if not RemoteMovieId.tableExists():
        RemoteMovieId.createTable()
    if not RemoteShowId.tableExists():
        RemoteShowId.createTable()
    #RemoteEpisodeId.createTable()
    if not LocalId.tableExists():
        LocalId.createTable()
    if not LocalMovieId.tableExists():
        LocalMovieId.createTable()
    if not LocalShowId.tableExists():
        LocalShowId.createTable()
    #LocalEpisodeId.createTable()
    if not Show.tableExists():
        Show.createTable()
    #Episode.createTable()
    if not TTL.tableExists():
        TTL.createTable()
    if not TCQueue.tableExists():
        TCQueue.createTable()

def close():
    from sqlobject import sqlhub
    try:
        sqlhub.processConnection.close()
    except AttributeError:
        Debug("[TraktCache] Closing cache before it was opened")
    
def _sync(xbmcData = None, traktData = None, cacheData = None):
    Debug("[TraktCache] Syncronising")
    #Debug("[~] "+repr(xbmcData)+"\n\n"+repr(traktData)+"\n\n"+repr(cacheData))
    
    if xbmcData is not None and ('movies' not in xbmcData or xbmcData['movies'] is None): xbmcData['movies'] = {}
    if traktData is not None and ('movies' not in traktData or traktData['movies'] is None): traktData['movies'] = {}
    if cacheData is not None and ('movies' not in cacheData or cacheData['movies'] is None): cacheData['movies'] = {}
    if xbmcData is not None and ('shows' not in xbmcData or xbmcData['shows'] is None): xbmcData['shows'] = {}
    if traktData is not None and ('shows' not in traktData or traktData['shows'] is None): traktData['shows'] = {}
    if cacheData is not None and ('shows' not in cacheData or cacheData['shows'] is None): cacheData['shows'] = {}
    if xbmcData is not None and ('episodes' not in xbmcData or xbmcData['episodes'] is None): xbmcData['episodes'] = {}
    if traktData is not None and ('episodes' not in traktData or traktData['episodes'] is None): traktData['episodes'] = {}
    if cacheData is not None and ('episodes' not in cacheData or cacheData['episodes'] is None): cacheData['episodes'] = {}
    
    #isolation testing
    #isolatedId = 'tvdb=76107@21x15'
    """if xbmcData is not None:
        xbmcData['movies'] = {}
        xbmcData['shows'] = {}
        if isolatedId in xbmcData['episodes']:
            xbmcData['episodes'] = {isolatedId: xbmcData['episodes'][isolatedId]}
        else:
            xbmcData['episodes'] = {}
    if traktData is not None:
        traktData['movies'] = {}
        traktData['shows'] = {}
        if isolatedId in traktData['episodes']:
            traktData['episodes'] = {isolatedId: traktData['episodes'][isolatedId]}
        else:
            traktData['episodes'] = {}"""
            
    # Find and list all changes
    #if xbmcData is not None:
        #for item in xbmcData['movies']:
        #    if item['remoteId'] == isolatedId:
        #        if item is not None: Debug("[~] X0"+repr(xbmcData['movies'][item]))
    #if traktData is not None:
        #for item in traktData['movies']:
        #    if item['remoteId'] == isolatedId:
        #        if item is not None: Debug("[~] T0"+repr(traktData['movies'][item]))
    
    # Find and list all changes
    if traktData is not None:
        xbmcChanges = _syncCompare(traktData, cache = cacheData)
        #for item in xbmcChanges['movies']:
        #    if item['remoteId'] == isolatedId:
        #        Debug("[~] X1"+repr(item))
    if xbmcData is not None:
        traktChanges = _syncCompare(xbmcData, xbmc = True, cache = cacheData)
        #for item in traktChanges['movies']:
        #    if item['remoteId'] == isolatedId:
        #        Debug("[~] T1"+repr(item))
        
    # Find unanimous changes and direct them to the cache
    cacheChanges = {}
    cacheChanges['movies'] = []
    cacheChanges['shows'] = []
    cacheChanges['episodes'] = []
    
    Debug("[TraktCache] Syncing - Culling changes")
    if traktData is not None and xbmcData is not None:
        for type in ['movies', 'shows', 'episodes']:
            removeListT = []
            removeListX = []
            for xbmcChange in xbmcChanges[type]:
                for traktChange in traktChanges[type]: # I think this works, but my concern is that it wont compare the values
                    if (xbmcChange['remoteId'] == traktChange['remoteId'] and xbmcChange['subject'] == traktChange['subject']):
                        removeListT.append(traktChange)
                        removeListX.append(xbmcChange)
                        if (xbmcChange['value'] <> traktChange['value']):
                            #Debug("[~] t"+repr(traktChange))
                            #Debug("[~] x"+repr(xbmcChange))
                            winingChange = traktChange
                            if 'weak' in winingChange: winingChange['weak'] = False
                            if xbmcChange['subject'] in ('playcount'):
                                if xbmcChange['value']>traktChange['value']:
                                    winingChange['value'] = xbmcChange['value']
                                else:
                                    winingChange['value'] = traktChange['value']
                            elif xbmcChange['subject'] in ('libraryStatus'):
                                winingChange['value'] = xbmcChange['value'] or traktChange['value']
                            cacheChanges[type].append(winingChange)
                        else:
                            cacheChanges[type].append(traktChange)
            for item in removeListT:
                try:
                    traktChanges[type].remove(item)   
                except ValueError:
                    continue
            for item in removeListX:
                try:
                    xbmcChanges[type].remove(item)
                except ValueError:
                    continue
    if traktData is not None:
        for type in ['movies', 'shows', 'episodes']:
            moveList = []
            for xbmcChange in xbmcChanges[type]:
                if 'weak' in xbmcChange and xbmcChange['weak']:
                    moveList.append(xbmcChange)
            for item in moveList:
                xbmcChanges[type].remove(item)
                cacheChanges[type].append(item)
    if xbmcData is not None:
        for type in ['movies', 'shows', 'episodes']:
            moveList = []
            for traktChange in traktChanges[type]:
                if 'weak' in traktChange and traktChange['weak']:
                    moveList.append(traktChange)
            for item in moveList:
                traktChanges[type].remove(item)
                cacheChanges[type].append(item)
    
    #if traktData is not None:
    #    for item in xbmcChanges['movies']:
    #        if item['remoteId'] == isolatedId:
    #            Debug("[~] X"+repr(item))
    #if xbmcData is not None:
    #    for item in traktChanges['movies']:
    #        if item['remoteId'] == isolatedId:
    #            Debug("[~] T"+repr(item))
    #for item in cacheChanges['movies']:
    #    if item['remoteId'] == isolatedId:
    #        Debug("[~] C"+repr(item))
                    
    
    Debug("[TraktCache] Syncing - Applying changes")
    # Perform cache only changes
    Debug("[TraktCache] Updating cache")
    _updateCache(cacheChanges, traktData)
    if traktData is not None:
        # Perform local (ie to xbmc) changes
        Debug("[TraktCache] Updating xbmc")
        _updateXbmc(xbmcChanges, traktData)
    if xbmcData is not None:
        # Log remote (ie to trakt) changes into queue and send to trakt
        Debug("[TraktCache] Updateing trakt")
        _updateTrakt(traktChanges, traktData)
    # Collate list of updated items
    remoteIds = []
    if traktData is not None:
        for type in ['movies', 'shows', 'episodes']:
            for remoteId in traktData[type]:
                remoteIds.append(remoteId)
    if xbmcData is not None:
        for type in ['movies', 'shows', 'episodes']:
            for remoteId in xbmcData[type]:
                remoteIds.append(remoteId)
    ## Update next sync times
    #updateSyncTimes(['library'], remoteIds)
    
##
# DB updaters
##

def _updateCache(changes, traktData = {}):
    toDebugFile(changes, 'cache')
    if 'movies' in changes:
        for change in changes['movies']:
            Debug("[TraktCache] Cache update: "+repr(change))
            if 'remoteId' in change and 'subject' in change and 'value' in change:
                if change['subject'] in ('title', 'year', 'runtime', 'released', 'tagline', 'overview', 'classification', 'playcount', 'rating', 'watchlistStatus', 'recommendedStatus', 'libraryStatus', 'traktDbStatus','trailer', 'poster', 'fanart'):
                    exists = change['remoteId'] in movies
                    if exists:
                        movie = movies[change['remoteId']]
                    if exists:
                        movie = movies[change['remoteId']]
                        
                        Debug("[TraktCache] Updating "+unicode(movie)+", setting "+str(change['subject'])+" to "+unicode(change['value']))
                        movie['_'+change['subject']] = change['value']
                        if 'bestBefore' in change:
                            movie._bestBefore[change['subject']] = change['bestBefore']
                        movies[change['remoteId']] = movie
                    else:
                        if 'movies' in traktData and change['remoteId'] in traktData['movies']:
                            Debug("[TraktCache] Inserting into cache from local trakt data: "+repr(traktData['movies'][change['remoteId']]))
                            movie = traktData['movies'][change['remoteId']]
                            if movie is not None:
                                movie.save()
                        else:
                            Debug("[TraktCache] Inserting into cache from remote trakt data")
                            movie = Movie.download(change['remoteId'])
                            if movie is not None:
                                movie.save()
    if 'shows' in changes:
        for change in changes['shows']:
            Debug("[TraktCache] Cache update: "+repr(change))
            if 'remoteId' in change and 'subject' in change and 'value' in change:
                if change['subject'] in ('title', 'year', 'firstAired', 'country', 'overview', 'runtime', 'network', 'airDay', 'airTime', 'classification', 'rating', 'watchlistStatus', 'recommendedStatus', 'libraryStatus', 'traktDbStatus', 'poster', 'fanart', 'episodes'):
                    exists = change['remoteId'] in shows
                    if exists:
                        show = shows[change['remoteId']]
                    if exists:
                        show = shows[change['remoteId']]
                        
                        Debug("[TraktCache] Updating "+unicode(show)+", setting "+str(change['subject'])+" to "+unicode(change['value']))
                        show['_'+change['subject']] = change['value']
                        if 'bestBefore' in change:
                            show._bestBefore[change['subject']] = change['bestBefore']
                        shows[change['remoteId']] = show
                    else:
                        if 'shows' in traktData and change['remoteId'] in traktData['shows']:
                            Debug("[TraktCache] Inserting into cache from local trakt data: "+repr(traktData['shows'][change['remoteId']]))
                            show = traktData['shows'][change['remoteId']]
                            if show is not None:
                                show.save()
                        else:
                            Debug("[TraktCache] Inserting into cache from remote trakt data")
                            show = Show.download(change['remoteId'])
                            if show is not None:
                                show.save()
    if 'episodes' in changes:
        for change in changes['episodes']:
            Debug("[TraktCache] Cache update: "+repr(change))
            if 'remoteId' in change and 'subject' in change and 'value' in change:
                if change['subject'] in ('title', 'overview', 'firstAired', 'playCount', 'rating', 'watchlistStatus', 'libraryStatus', 'screen'):
                    exists = change['remoteId'] in episodes
                    if exists:
                        episode = episodes[change['remoteId']]
                    if exists:
                        episode = episodes[change['remoteId']]
                        
                        Debug("[TraktCache] Updating "+unicode(episode)+", setting "+str(change['subject'])+" to "+unicode(change['value']))
                        episode['_'+change['subject']] = change['value']
                        if 'bestBefore' in change:
                            episode._bestBefore[change['subject']] = change['bestBefore']
                        episodes[change['remoteId']] = episode
                    else:
                        if 'episodes' in traktData and change['remoteId'] in traktData['episodes']:
                            Debug("[TraktCache] Inserting into cache from local trakt data: "+repr(traktData['episodes'][change['remoteId']]))
                            episode = traktData['episodes'][change['remoteId']]
                            if episode is not None:
                                episode.save()
                        else:
                            Debug("[TraktCache] Inserting into cache a shell episode")
                            episode = Episode(change['remoteId'], static=True)
                            if episode is not None:
                                episode.save()

def _updateXbmc(changes, traktData = {}):
    cacheChanges = {}
    toDebugFile(changes, 'xbmc')
    
    if 'movies' in changes:
        cacheChanges['movies'] = []
        for change in changes['movies']:
            Debug("[TraktCache] XBMC update: "+repr(change))
            if 'remoteId' in change and 'subject' in change and 'value' in change:
                if change['subject'] == 'playcount':
                    if setXBMCMoviePlaycount(Movie.devolveId(change['remoteId']), change['value']) is None:
                        continue # failed, skip
                elif change['subject'] in ('title', 'year', 'runtime', 'released', 'tagline', 'overview', 'classification', 'rating', 'watchlistStatus', 'recommendedStatus', 'libraryStatus', 'trailer', 'poster', 'fanart'):
                    # ignore, irrelevant, pass on to update the cache
                    pass
                else:
                    # invalid
                    continue
                # succeeded
                cacheChanges['movies'].append(change)
    if 'shows' in changes:
        cacheChanges['shows'] = []
        for change in changes['shows']:
            Debug("[TraktCache] XBMC update: "+repr(change))
            if 'remoteId' in change and 'subject' in change and 'value' in change:
                if change['subject'] in ('title', 'year', 'firstAired', 'country', 'overview', 'runtime', 'network', 'airDay', 'airTime', 'classification', 'rating', 'watchlistStatus', 'recommendedStatus', 'libraryStatus', 'poster', 'fanart', 'episodes'):
                    # ignore, irrelevant, pass on to update the cache
                    pass
                else:
                    # invalid
                    continue
                # succeeded
                cacheChanges['shows'].append(change)
    if 'episodes' in changes:
        cacheChanges['episodes'] = []
        for change in changes['episodes']:
            Debug("[TraktCache] XBMC update: "+repr(change))
            if 'remoteId' in change and 'subject' in change and 'value' in change:
                if change['subject'] == 'playcount':
                    showId, season, episode = Episode.devolveId(change['remoteId'])
                    if setXBMCEpisodePlaycount(showId, season, episode, change['value']) is None:
                        continue # failed, skip
                elif change['subject'] in ('title', 'overview', 'firstAired', 'rating', 'watchlistStatus', 'libraryStatus', 'screen'):
                    # ignore, irrelevant, pass on to update the cache
                    pass
                else:
                    # invalid
                    continue
                # succeeded
                cacheChanges['episodes'].append(change)
    _updateCache(cacheChanges, traktData)        

def _updateTrakt():
    """
    Update trakt if possible, draws from the cache of updates,
    any successful updates are removed from the queue and
    applied to the cache, any that are not successful are left
    in the queue to be processes when possible
    """

    queue = TCQueue.selectBy(dest='trakt') # Select all changes for trakt
    for change in queue.lazyIter(): # Iterate over them, getting them one by one
        if isinstance(change.instance, Movie): # If this one is a movie
            Debug("[TraktCache] trakt update: "+repr(change))
            subject = change.subject
            if subject == 'watchlistStatus':
                if change.value == True:
                    if Trakt.movieWatchlist([Movie(change['remoteId']).traktise()]) is None:
                        continue # failed, leave in queue for next time
                else:
                    if Trakt.movieUnwatchlist([Movie(change['remoteId']).traktise()]) is None:
                        continue # failed, leave in queue for next time
            elif subject == 'playcount':
                movie = change.instance
                if (movie._playcount >= 0):
                    if (movie._playcount == 0):
                        if Trakt.movieUnseen([movie.traktise()]) is None:
                            continue # failed, leave in queue for next time
                    else:
                        if Trakt.movieSeen([movie.traktise()]) is None:
                            continue # failed, leave in queue for next time
                movie._playcount = change.value
            elif subject == 'libraryStatus':
                if change.value == True:
                    if Trakt.movieLibrary([change.instance.traktise()]) is None:
                        continue # failed, leave in queue for next time
                else:
                    result = Trakt.movieUnlibrary([change.instance.traktise()], returnStatus = True)
                    Debug('[TraktCache] _updateTrakt, libraryStatus, unlibrary, responce: '+str(result))
                    if 'error' in result: continue # failed, leave in queue for next time
            elif subject == 'rating':
                movie = change.instance.traktise()
                if Trakt.rateMovie(movie['imdb_id'], movie['title'], movie['year'], change['value'], movie['tmdb_id']) is None:
                    continue # failed, leave in queue for next time
            elif subject in ('title', 'year', 'runtime', 'released', 'tagline', 'overview', 'classification', 'rating', 'trailer', 'poster', 'fanart'):
                # ignore, irrelevant, pass on to update the cache
                pass
            else:
                # invalid, destroy change
                change.destroySelf()
                continue
            # succeeded, pass to cache
            change.dest = 'cache'
        if isinstance(change.instance, Show): # If this one is a show
            Debug("[TraktCache] trakt update: "+repr(change))
            if 'remoteId' in change and 'subject' in change and 'value' in change:
                if change['subject'] == 'watchlistStatus':
                    if change['value'] == True:
                        if Trakt.showWatchlist([Show(change['remoteId']).traktise()]) is None:
                            continue # failed, leave in queue for next time
                    else:
                        if Trakt.showUnwatchlist([Show(change['remoteId']).traktise()]) is None:
                            continue # failed, leave in queue for next time
                elif change['subject'] == 'rating':
                    show = Show(change['remoteId']).traktise()
                    if Trakt.rateShow(show['tvdb_id'], show['title'], show['year'], change['value'], show['imdb_id']) is None:
                        continue # failed, leave in queue for next time
                elif change['subject'] in ('title', 'year', 'firstAired', 'country', 'overview', 'runtime', 'network', 'airDay', 'airTime', 'classification', 'recommendedStatus', 'poster', 'fanart', 'episodes'):
                    # ignore, irrelevant, pass on to update the cache
                    pass
                else:
                    # invalid
                    queue = shows['_queue']
                    queue.remove(change)
                    shows['_queue'] = queue
                    continue
                # succeeded
                cacheChanges['shows'].append(change)
            # either succeeded or invalid
            queue = shows['_queue']
            queue.remove(change)
            shows['_queue'] = queue
    if 'episodes' in changeQueue:
        for item in changeQueue['episodes']:
            Debug("[~] E> "+str(item['subject'])+"\t "+str(item['remoteId'])+"\t "+str(item['value']))
        cacheChanges['episodes'] = []
        for change in changeQueue['episodes']:
            Debug("[TraktCache] trakt update: "+repr(change))
            if 'remoteId' in change and 'subject' in change and 'value' in change:
                if change['subject'] == 'watchlistStatus':
                    if change['value'] == True:
                        if Trakt.showEpisodeWatchlist([Episode(change['remoteId']).traktise()]) is None:
                            continue # failed, leave in queue for next time
                    else:
                        if Trakt.showEpisodeUnwatchlist([Episode(change['remoteId']).traktise()]) is None:
                            continue # failed, leave in queue for next time
                elif change['subject'] == 'playcount':
                    episode = Episode(change['remoteId']).traktise()
                    if (change['value'] >= 0):
                        if (change['value'] == 0):
                            if Trakt.showEpisodeUnseen(episode['tvdb_id'], episode['title'], episode['year'], [{'season': episode['season'], 'episode': episode['episode']}], episode['imdb_id']) is None:
                                continue # failed, leave in queue for next time
                        else:
                            if Trakt.showEpisodeSeen(episode['tvdb_id'], episode['title'], episode['year'], [{'season': episode['season'], 'episode': episode['episode']}], episode['imdb_id']) is None:
                                continue # failed, leave in queue for next time
                elif change['subject'] == 'libraryStatus':
                    episode = Episode(change['remoteId']).traktise()
                    if change['value'] == True:
                        if Trakt.showEpisodeLibrary(episode['tvdb_id'], episode['title'], episode['year'], [{'season': episode['season'], 'episode': episode['episode']}], episode['imdb_id']) is None:
                            continue # failed, leave in queue for next time
                    else:
                        if Trakt.showEpisodeUnlibrary(episode['tvdb_id'], episode['title'], episode['year'], [{'season': episode['season'], 'episode': episode['episode']}], episode['imdb_id']) is None:
                            continue # failed, leave in queue for next time
                elif change['subject'] == 'rating':
                    episode = Episode(change['remoteId']).traktise()
                    if Trakt.rateEpisode(episode['tvdb_id'], episode['showtitle'], episode['year'], episode['season'], episode['episode'], change['value'], episode['imdb_id']) is None:
                        continue # failed, leave in queue for next time
                elif change['subject'] in ('title', 'overview', 'firstAired', 'screen'):
                    # ignore, irrelevant, pass on to update the cache
                    pass
                else:
                    # invalid
                    queue = episodes['_queue']
                    queue.remove(change)
                    episodes['_queue'] = queue
                    continue
                # succeeded
                cacheChanges['episodes'].append(change)
            # either succeeded or invalid
            queue = episodes['_queue']
            queue.remove(change)
            episodes['_queue'] = queue
    _updateCache(cacheChanges, traktData)

def toDebugFile(changes, destination):
    cacheDirectory = "special://profile/addon_data/script.TraktUtilities/"
    try:
        myFile = open(xbmc.translatePath(os.path.join(cacheDirectory,"changes.csv")), 'a+')
    except IOError:
        myFile = open(xbmc.translatePath(os.path.join(cacheDirectory,"changes.csv")), 'w')
        myFile.write("destination,type,remoteId,subject,value\n")
    if changes is None: return
    for type in changes:
        if changes[type] is None: continue
        for change in changes[type]:
            if type == 'episodes':
                ep = getEpisode(change['remoteId'])
                if ep is None or change['remoteId'] is None:
                    title = change['remoteId']
                else:
                    show = getShow(ep._showRemoteId)
                    if show is None or ep._showRemoteId is None:
                        title = change['remoteId']
                    else:
                        title = str(show._title) +" ("+ str(show._year) +") "+ str(ep._season) +"x"+ str(ep._episode)
            if type == 'movies':
                movie = getMovie(change['remoteId'])
                if movie is None or change['remoteId'] is None:
                    title = change['remoteId']
                else:
                    title = str(movie._title) +" ["+ str(movie._year)+"]"
            if type == 'shows':
                show = getShow(change['remoteId'])
                if show is None or change['remoteId'] is None:
                    title = change['remoteId']
                else:
                    title = str(show._title) +" ["+ str(show._year)+"]"
            myFile.write(str(destination)+","+str(str(type))+","+str(title)+","+str(change['subject'])+","+str(change['value'])+"\n")
    myFile.close()

##
# DB Readers
##

@async
def _copyTraktMovies():
    movies = {}
    traktMovies = AsyncCall(Trakt.userLibraryMoviesAll, None, username, daemon=True)
    watchlistMovies = AsyncCall(Trakt.userWatchlistMovies, None, username)
    
    traktMovies = ~traktMovies
    watchlistMovies = ~watchlistMovies
    
    Debug("[~] :"+str(len(traktMovies)))
    
    if traktMovies is None: return movies
    watchlistMovies = traktMovieListByImdbID(watchlistMovies)
    for movie in traktMovies:
        local = Movie.fromTrakt(movie)
        if local is None:
            continue
        if watchlistMovies is not None and 'imdb_id' in movie:
            local._watchlistStatus = movie['imdb_id'] in watchlistMovies
        movies[local._remoteId] = local
    return movies

@async
def _copyTraktShows():
    shows = {}
    traktShows = Trakt.userLibraryShowsAll(username, daemon=True)
    
    for show in traktShows:
        local = Show.fromTrakt(show)
        if local is None:
            continue
        shows[local._remoteId] = local
    return shows

@async
def _copyTraktEpisodes():
    episodes = {}
    traktShowsCollection = Trakt.userLibraryShowsCollection(username, daemon=True)
    
    for show in traktShowsCollection:
        local = Show.fromTrakt(show)
        if local is None: continue
        remoteId = local._remoteId
        for season in show['seasons']:
            s = season['season']
            for e in season['episodes']:
                episode = Episode(str(remoteId)+'@'+str(s)+'x'+str(e), static=True)
                episode._libraryStatus = True;
                episodes[episode._remoteId] = episode
    return episodes
    
def _copyTrakt():
    traktData = {}
                        
    movies = _copyTraktMovies()
    shows = _copyTraktShows()
    episodes = _copyTraktEpisodes()
        
    traktData['movies'] = ~movies
    traktData['shows'] = ~shows
    traktData['episodes'] = ~episodes
    
    return traktData    

def _copyXbmc():
    xbmcData = {}
    
    movies = {}
    xbmcMovies = getMoviesFromXBMC()
    for movie in xbmcMovies:
        local = Movie.fromXbmc(movie)
        if local is None:
            continue
        movies[local._remoteId] = local
    
    shows = {}
    xbmcShows = getTVShowsFromXBMC()['tvshows']
    for show in xbmcShows:
        local = Show.fromXbmc(show)
        if local is None:
            continue
        shows[local._remoteId] = local
        
    episodes = {}
    for show in xbmcShows:
        remoteId = Show.fromXbmc(show)._remoteId
        seasons = getSeasonsFromXBMC(show)
        if seasons is not None and 'seasons' in seasons:
            seasons = seasons['seasons']
            for season in seasons:
                s = season['season']
                xbmcEpisodes = getEpisodesFromXBMC(show, s)
                if xbmcEpisodes is not None and 'episodes' in xbmcEpisodes:
                    xbmcEpisodes = xbmcEpisodes['episodes']
                    for episode in xbmcEpisodes:
                        episode = Episode.fromXbmc(remoteId, episode)
                        if episode is not None:
                            episodes[episode._remoteId] = episode
        
    xbmcData['movies'] = movies
    xbmcData['shows'] = shows
    xbmcData['episodes'] = episodes
    return xbmcData

##
# Sync comparitors
##

attributes = {
    'xbmc': {
        'movies': {
            'primary': ['playcount', 'trailer', 'poster', 'fanart'],
            'secondary': ['title', 'year', 'runtime', 'tagline']
        },
        'shows': {
            'primary': ['fanart'],
            'secondary': ['title', 'year']
        },
        'episodes': {
            'primary': ['playcount', 'screen'],
            'secondary': ['title', 'firstAired', 'runtime']
        }
    },
    'trakt': {
        'movies': {
            'primary': ['title', 'year', 'runtime', 'released', 'tagline', 'overview', 'classification', 'playcount', 'rating', 'watchlistStatus', 'recommendedStatus', 'traktDbStatus'],
            'secondary': ['trailer', 'poster', 'fanart', 'libraryStatus']
        },
        'shows': {
            'primary': ['rating', 'watchlistStatus', 'recommendedStatus', 'traktDbStatus'],
            'secondary': ['poster', 'fanart']
        },
        'episodes': {
            'primary': ['playcount', 'rating', 'watchlistStatus'],
            'secondary': ['screen', 'libraryStatus']
        }
    }
}

def _syncCompare(data, xbmc = False, cache = None):
    if xbmc:
        attr = attributes['xbmc']
    else :
        attr = attributes['trakt']
    changes = {}
    if cache is None:
        # Compare movies
        changes['movies'] = _listChanges(data['movies'], movies, attr['movies']['primary'],  attr['movies']['secondary'], xbmc, writeBack = movies)
        # Compare TV shows
        changes['shows'] = _listChanges(data['shows'], shows, attr['shows']['primary'],  attr['shows']['secondary'], xbmc, writeBack = shows)
        # Compare TV episodes
        changes['episodes'] = _listChanges(data['episodes'], episodes, attr['episodes']['primary'],  attr['episodes']['secondary'], xbmc, writeBack = episodes)
    else:
        # Compare movies
        changes['movies'] = _listChanges(data['movies'], cache['movies'], attr['movies']['primary'],  attr['movies']['secondary'], xbmc, writeBack = movies)
        # Compare TV shows
        changes['shows'] = _listChanges(data['shows'], cache['shows'], attr['shows']['primary'],  attr['shows']['secondary'], xbmc, writeBack = shows)
        # Compare TV episodes
        changes['episodes'] = _listChanges(data['episodes'], cache['episodes'], attr['episodes']['primary'],  attr['episodes']['secondary'], xbmc, writeBack = episodes)
    return changes

def _listChanges(newer, older, attributes, weakAttributes, xbmc = False, writeBack = None):
    changes = []
    # Find new items
    remoteIds = newer.keys()   
    for remoteId in remoteIds:
        if remoteId is None: continue
        if not validRemoteId(remoteId): continue
        newItem = newer[remoteId]
        if newItem is None: continue
        if newItem._remoteId not in older:
            if xbmc: changes.append({'remoteId': remoteId, 'subject': 'libraryStatus', 'value':True, 'weak': True})
            for attribute in attributes:
                if newItem['_'+attribute] is not None: changes.append({'remoteId': remoteId, 'subject': attribute, 'value':newItem['_'+attribute], 'weak': True, 'bestBefore': time.time()+24*60*60})
            for attribute in weakAttributes:
                if newItem['_'+attribute] is not None: changes.append({'remoteId': remoteId, 'subject': attribute, 'value':newItem['_'+attribute], 'weak': True, 'bestBefore': time.time()+24*60*60})
    
    remoteIds = older.keys()    
    for remoteId in remoteIds:
        if len(remoteId) == 0: continue
        if not validRemoteId(remoteId): continue
        oldItem = older[remoteId]
        if oldItem is None:
            continue
        if remoteId not in newer: #If item not in library
            if xbmc:
                if oldItem['_libraryStatus']: #If item had been in library
                    changes.append({'remoteId': remoteId, 'subject': 'libraryStatus', 'value':False})
        else:
            newItem = newer[remoteId]
            if newItem is None:
                continue
            for attribute in attributes:
                if attribute == 'episodes':
                    if _episodesDifferent(newItem['_'+attribute], oldItem['_'+attribute]): # If the non cached data is different from the old data cached locally
                        if newItem['_'+attribute] is not None: changes.append({'remoteId': remoteId, 'subject': attribute, 'value':newItem['_'+attribute]})
                if newItem['_'+attribute] <> oldItem['_'+attribute]: # If the non cached data is different from the old data cached locally
                    if newItem['_'+attribute] is not None: changes.append({'remoteId': remoteId, 'subject': attribute, 'value':newItem['_'+attribute], 'weak': (oldItem['_'+attribute] is None)})
                oldItem._bestBefore[attribute] = time.time()+24*60*60
            for attribute in weakAttributes:
                if oldItem['_'+attribute] is None: # If the non cached data is different from the old data cached locally
                    if newItem['_'+attribute] is not None: changes.append({'remoteId': remoteId, 'subject': attribute, 'value':newItem['_'+attribute], 'weak': True})
                oldItem._bestBefore[attribute] = time.time()+24*60*60
        oldItem._bestBefore['libraryStatus'] = time.time()+12*60*60
        if writeBack is None:
            pass
        else:
            writeBack[remoteId] = oldItem
    return changes
    
def _episodesDifferent(newEpisodes, oldEpisodes):
    diff = set(newEpisodes.keys()) - set(oldEpisodes.keys())
    if diff.length <> 0: return True
    for season in newEpisodes:
        diff = set(newEpisodes[season].keys()) - set(oldEpisodes[season].keys())
        if diff.length <> 0: return True
    return False
    
def makeChanges(changes, traktOnly = False, xbmcOnly = False):
    Debug("[~] Made changes: "+repr(changes))
    if not traktOnly: _updateXbmc(changes)
    if not xbmcOnly: _updateTrakt(changes)

##
# Sync timing
##

def trigger():
    Debug("[TraktCache] Starting triggered updates")
    try:
        Debug("[TraktCache] Getting partial list of changes")
        if not getActivityUpdates(): # if the activity updates might ve missing some data
            Debug("[TraktCache] Getting extended list of changes")
            needSyncAtLeast(['library', 'watchlist'], force=True)
        Debug("[TraktCache] Updating stale sets")
        needSyncAtLeast(['all'])
        Debug("[TraktCache] All triggered updates complete")
    except TUSyncFailed, e:
        Debug("[TraktCache] Unable to complete triggered updates: "+str(e))

_setStucture = {
    'all': {
        'movieall': {
            'movielibrary': {},
            'movierecommended': {},
            'moviewatchlist': {},
        },
        'showall': {
            'showrecommended': {},
            'showwatchlist': {},
        },
        'episodeall': {
            'episodelibrary': {},
            'episodewatchlist': {},
        },
        'library': {
            'movielibrary': {},
            'episodelibrary': {},
        },
        'movielibrary': {
            'movieseen': {},
        },
        'episodelibrary': {
            'episodeseen': {},
        },
        'watchlist': {
           'moviewatchlist': {},
           'showwatchlist': {},
           'episodewatchlist': {},
        },
    }
}
    
syncTimes = {'episodelibrary': timedelta(hours=6),
             'episodeseen': timedelta(hours=3),
             'episodewatchlist': timedelta(minutes=10),
             'episodeimages': timedelta(hours=12),
             'episodeall': timedelta(hours=24),
             'showrecommended': timedelta(hours=1),
             'showwatchlist': timedelta(minutes=10),
             'showimages': timedelta(hours=12),
             'showall': timedelta(hours=24),
             'moviewatchlist': timedelta(minutes=10),
             'movierecommended': timedelta(hours=1),
             'movieseen': timedelta(hours=3),
             'movielibrary': timedelta(hours=6),
             'movieimages': timedelta(hours=12),
             'movieall': timedelta(hours=24),
             'library': timedelta(hours=1),
             'watchlist': timedelta(minutes=30),
             'all': timedelta(hours=24),
             'useractivity': timedelta(hours=2),
             'friendsactivity': timedelta(hours=3)}

def getActivityUpdates(force=False):
    userActCount = 0
    friendsActCount = 0

    if checkTTL('useractivity') or force:
        timeStamp, userActCount = refreshFromUserActivity(getTTL('useractivity'))
        setTTL('useractivity', datetime.fromtimestamp(timeStamp))

    if checkTTL('friendsactivity') or force:
        checkFriendsActivity = getTTL('friendsactivity')

    """if checkFriendsActivity <> -1:
        timeStamp, friendsActCount = refreshFromFriendsActivity(checkFriendsActivity)
        expire['friendsactivity'] = timeStamp"""
    if userActCount >= 100 or friendsActCount >= 100:
        return False
    return True

def getTTL(name):
    entries = TTL.selectBy(name=name)
    try:
        expire = entries.getOne()
        Debug(str(expire.time))
        return expire.time
    except SQLObjectNotFound:
        return datetime.min
    except SQLObjectIntegrityError:
        Debug("[TraktCache] getTTL, Warning integiry error, multiple results for one set")
        return datetime.min

def checkTTL(name):
    return (getTTL(name)+syncTimes[name]) < datetime.now()

def setTTL(name, time):
    results = TTL.selectBy(name=name)
    try:
        results.getOne().time = time
    except SQLObjectNotFound:
        Debug("[TTL] Note: expirery not found adding set as new: "+str(name))
        TTL(name=name, time=time)
    except SQLObjectIntegrityError:
        Debug("[TTL] Warning integiry error, multiple results for one set")

def updateSyncTimes(sets = [], remoteIds = []):
    updated = {}
    sets = set(sets)
    sets, _ = setPropergatePositive(sets, _setStucture)
    
    for updatedSet in sets:
        if updatedSet not in syncTimes:
            Debug("[TraktCache] Tried to bump update time of unknown update set:" +updatedSet)
            continue
        Debug("[TraktCache] Updating timestamp for "+str(updatedSet))
        setTTL(updatedSet, datetime.now())
    for remoteId in remoteIds:
        expire[remoteId] = datetime.now() + 10*60 # +10mins

def setPropergatePositive(sets, structure):
    more = True
    found = False
    done = set([])
    checked = set([])
    while more:
        more = False
        for item in structure:
            if item in sets and item not in done:
                sets |= set(structure[item].keys())
                done.add(item)
                checked.discard(item)
                found = True
                more = True
            subFound = False
            if item not in checked:
                sets, subFound = setPropergatePositive(sets, structure[item])
                checked.add(item)
            if subFound:
                more = True
                found = True
    return sets, found

def needSyncAtLeast(sets = [], movieIds = [], showIds = [], episodeIds = [], force = False):
    from trakt import TraktRequestFailed
    # This function should block untill all syncs have been satisfied, unless a Trakt request failed
    try:
        sets = set(sets)
        sets = setPropergateNegative(sets, _setStucture)
        for staleSet in sets:
            if checkTTL(staleSet) or force:
                refreshSet(staleSet)
        for remoteId in movieIds:
            if checkTTL(remoteId) or force:
                refreshMovie(remoteId)
        for remoteId in showIds:
            if checkTTL(remoteId) or force:
                refreshShow(remoteId)
        for remoteId in episodeIds:
            if checkTTL(remoteId) or force:
                refreshEpisode(remoteId)
    except TraktRequestFailed, e:
        mutate(TUSyncFailed, "Failed trakt.tv request prevented syncing: ")
    return

def setPropergateNegative(sets, structure, fireSale=False):
    for item in structure:
        if fireSale or item in sets:
            sets -= set(structure[item].keys())
            sets = setPropergateNegative(sets, structure[item], fireSale=True)
        else:
            sets = setPropergateNegative(sets, structure[item])
    return sets

##
# Items
##

def getMovie(remoteId = None, localId = None):
    if remoteId is None and localId is None:
        raise ValueError("Must provide at least one form of id")
    if remoteId is None:
        remoteId = getMovieRemoteId(localId)
    if remoteId is None:
        return None
    if remoteId not in movies:
        return None
    return movies[remoteId]

def getShow(remoteId = None, localId = None):
    if remoteId is None and localId is None:
        raise ValueError("Must provide at least one form of id")
    if remoteId is None:
        remoteId = getShowRemoteId(localId)
    if remoteId is None:
        return None
    if remoteId not in shows:
        return None
    return shows[remoteId]
        
def getEpisode(remoteId = None, localId = None):
    if remoteId is None and localId is None:
        raise ValueError("Must provide at least one form of id")
    if remoteId is None:
        remoteId = getEpisodeRemoteId(localId)
    if remoteId is None:
        return None
    if remoteId not in episodes:
        return None
    return episodes[remoteId]
        
def getMovieRemoteId(localId):
    if '_byLocalId' in movies and localId in movies['_byLocalId']:
        return movies['_byLocalId'][localId]
    return None     
    
def getShowRemoteId(localId):
    if '_byLocalId' in shows and localId in shows['_byLocalId']:
        return shows['_byLocalId'][localId]
    return None
            
def getEpisodeRemoteId(localId):
    if '_byLocalId' in episodes and localId in episodes['_byLocalId']:
        return episodes['_byLocalId'][localId]
    return None

def getMovieLocalIds(remoteId):
    hits = []
    for localId in movies['_byLocalId']:
        if remoteId == movies['_byLocalId'][localId]:
            hits.append(localId)
    return hits
    
def getShowLocalIds(remoteId):
    hits = []
    for localId in shows['_byLocalId']:
        if remoteId == shows['_byLocalId'][localId]:
            hits.append(localId)
    return hits
    
def getEpisodeLocalIds(remoteId):
    hits = []
    for localId in episodes['_byLocalId']:
        if remoteId == episodes['_byLocalId'][localId]:
            hits.append(localId)
    return hits

def relateMovieId(localId, remoteId):
    if '_byLocalId' in movies:
        index = movies['_byLocalId']
    else:
        index = {}
    index[localId] = remoteId
    movies['_byLocalId'] = index
        
def relateShowId(localId, remoteId):
    if '_byLocalId' in shows:
        index = shows['_byLocalId']
    else:
        index = {}
    index[localId] = remoteId
    shows['_byLocalId'] = index
        
def relateEpisodeId(localId, remoteId):
    if '_byLocalId' in episodes:
        index = episodes['_byLocalId']
    else:
        index = {}
    index[localId] = remoteId
    episodes['_byLocalId'] = index

def refreshShow(remoteId, property = None):
    localIds = getShowLocalIds(remoteId)
    if len(localIds) == 0:
        localId = None
    else:
        localId  = localIds[0]
    xbmcData = None
    cacheData = None
    if localId is not None:
        show = Show.fromXbmc(getShowDetailsFromXbmc(localId,['title', 'year']))
        if show is not None:
            xbmcData = {'shows': {remoteId: show}}
        else:
            xbmcData = {'shows': {}}
    if property is not None:
        if property in ('title', 'year', 'firstAired', 'country', 'overview', 'runtime', 'network', 'airDay', 'airTime', 'classification', 'rating', 'watchlistStatus', 'poster', 'fanart', 'episodes'):
            show = Show.download(remoteId)
            if show is not None:
                traktData = {'shows': {remoteId: show}}
            else:
                traktData = {'shows': {}}
        elif property in ('recommendedStatus'):
            refreshRecommendedShows()
            return
    else:
        traktData = {'shows': {remoteId: Show.download(remoteId)}}
    if remoteId in shows:
        cacheData = {'shows': {remoteId: shows[remoteId]}}
            
    _sync(xbmcData, traktData, cacheData)
    
    expire[remoteId] = time.time() + 10*60 # +10mins

def refreshEpisode(remoteId, property = None):
    localIds = getEpisodeLocalIds(remoteId)
    if len(localIds) == 0:
        localId = None
    else:
        localId  = localIds[0]
    xbmcData = None
    cacheData = None
    if localId is not None:
        episode = Episode.fromXbmc(getEpisodeDetailsFromXbmc(localId,['title', 'year']))
        if episode is not None:
            xbmcData = {'episodes': {remoteId: episode}}
        else:
            xbmcData = {'episodes': {}}
    if property is not None:
        if property in ('title', 'overview', 'classification', 'playcount', 'rating', 'firstAired', 'watchlistStatus', 'libraryStatus', 'screen', 'fanart'):
            episode = Episode.download(remoteId)
            if episode is not None:
                traktData = {'episodes': {remoteId: show}}
            else:
                traktData = {'episodes': {}}
    else:
        traktData = {'episodes': {remoteId: Episode.download(remoteId)}}
    if remoteId in shows:
        cacheData = {'episodes': {remoteId: episodes[remoteId]}}
            
    _sync(xbmcData, traktData, cacheData)
    
    expire[remoteId] = time.time() + 10*60 # +10mins

def saveMovie(movie):
    movies[movie._remoteId] = movie
        
def saveShow(show):
    shows[show._remoteId] = show
        
def saveEpisode(episode):
    episodes[episode._remoteId] = episode

def newLocalMovie(localId):
    movie = Movie.fromXbmc(getMovieDetailsFromXbmc(localId,['title', 'year', 'originaltitle', 'imdbnumber', 'playcount', 'lastplayed', 'runtime']))
    movie.save()
    relateMovieId(localId, movie._remoteId)
    movie.refresh()
  
    
##
# Activity Updates
##

def refreshFromUserActivity(lastTimestamp):
    try:
        responce = Trakt.activityUsers(username, timestamp=lastTimestamp)
    except TraktRequestFailed, e:
        mutate(TUSyncFailed, "Failed trakt.tv request prevented syncing: ")
    changes = {}
    changes['episodes'] = []
    changes['movies'] = []
    changes['shows'] = []
    for event in responce['activity']:
        Debug("Update activity, "+str(event['type'])+'/'+str(event['action']))
        if event['type'] == 'episode':
            if event['action'] == 'watching':
                continue #ignore
            if event['action'] == 'scrobble':
                episode = Episode.fromTrakt(event['show'], event['episode'])
                changes['episodes'].append({'remoteId': episode._remoteId, 'subject': 'playcount', 'value':episode._playcount, 'bestBefore': time.time()+6*60*60})
            if event['action'] == 'checkin':
                continue #ignore
            if event['action'] == 'seen':
                for traktEpisode in event['episodes']:
                    episode = Episode.fromTrakt(event['show'], event['episode'])
                changes['episodes'].append({'remoteId': episode._remoteId, 'subject': 'playcount', 'value':episode._playcount, 'bestBefore': time.time()+6*60*60})
            if event['action'] == 'collection':
                for traktEpisode in event['episodes']:
                    episode = Episode.fromTrakt(event['show'], traktEpisode)
                    changes['episodes'].append({'remoteId': episode._remoteId, 'subject': 'libraryStatus', 'value':episode._libraryStatus, 'bestBefore': time.time()+6*60*60})
            if event['action'] == 'rating':
                episode = Episode.fromTrakt(event['show'], event['episode'])
                changes['episodes'].append({'remoteId': episode._remoteId, 'subject': 'rating', 'value':episode._rating, 'bestBefore': time.time()+6*60*60})
            if event['action'] == 'watchlist':
                episode = Episode.fromTrakt(event['show'], event['episode'])
                changes['episodes'].append({'remoteId': episode._remoteId, 'subject': 'watchlistStatus', 'value':episode._watchlistStatus, 'bestBefore': time.time()+6*60*60})
            if event['action'] == 'shout':
                continue #ignore
        if event['type'] == 'show':
            if event['action'] == 'rating':
                show = Show.fromTrakt(event['show'])
                changes['shows'].append({'remoteId': show._remoteId, 'subject': 'rating', 'value':show._rating, 'bestBefore': time.time()+6*60*60})
            if event['action'] == 'watchlist':
                show = Show.fromTrakt(event['show'])
                changes['shows'].append({'remoteId': show._remoteId, 'subject': 'watchlistStatus', 'value':show._watchlistStatus, 'bestBefore': time.time()+6*60*60})
            if event['action'] == 'shout':
                continue #ignore
        if event['type'] == 'movie':
            if event['action'] == 'watching':
                continue #ignore
            if event['action'] == 'scrobble':
                movie = Movie.fromTrakt(event['movie'])
                changes['movies'].append({'remoteId': movie._remoteId, 'subject': 'playcount', 'value':movie._playcount, 'bestBefore': time.time()+6*60*60})
            if event['action'] == 'checkin':
                continue #ignore
            if event['action'] == 'seen':
                movie = Movie.fromTrakt(event['movie'])
                changes['movies'].append({'remoteId': movie._remoteId, 'subject': 'playcount', 'value':movie._playcount, 'bestBefore': time.time()+6*60*60})
            if event['action'] == 'collection':
                movie = Movie.fromTrakt(event['movie'])
                changes['movies'].append({'remoteId': movie._remoteId, 'subject': 'libraryStatus', 'value':movie._libraryStatus, 'bestBefore': time.time()+6*60*60})
            if event['action'] == 'rating':
                movie = Movie.fromTrakt(event['movie'])
                changes['movies'].append({'remoteId': movie._remoteId, 'subject': 'rating', 'value':movie._rating, 'bestBefore': time.time()+6*60*60})
            if event['action'] == 'watchlist':
                movie = Movie.fromTrakt(event['movie'])
                changes['movies'].append({'remoteId': movie._remoteId, 'subject': 'watchlistStatus', 'value':movie._watchlistStatus, 'bestBefore': time.time()+6*60*60})
            if event['action'] == 'shout':
                continue #ignore
    
    _updateXbmc(changes) 
    return responce['timestamps']['current'], len(responce['activity'])
    
def refreshFromFriendsActivity(lastTimestamp):
    raise NotImplementedError("This function has not been written")
    
"""def compareNewer(xbmcData=None, traktData=None):
    if xbmcData is None and traktData is None:
        return
    cacheData = {}
    cacheData['movies'] = []
    for movie in xbmcData['movies']:
        item = getMovie(movie._remoteId)
        if item is not None:
            cacheData['movies'].append(item)
    cacheData['shows'] = []
    for show in xbmcData['shows']:
        item = getShow(show._remoteId)
        if item is not None:
            cacheData['shows'].append(item)
    cacheData['episodes'] = []
    for episode in xbmcData['episodes']:
        item = getEpisode(episode._remoteId)
        if item is not None:
            cacheData['episodes'].append(item)
    if xbmcData is None:
        xbmcData = {}
        xbmcData['movies'] = []
        for movie in xbmcData['movies']:
            localIds = getMovieLocalIds(remoteId)
            if len(localIds) > 0:
                item = Movie.fromXbmc(getMovieDetailsFromXbmc(localIds[0],['title', 'year', 'originaltitle', 'imdbnumber', 'playcount', 'lastplayed', 'runtime']))
                if item is not None:
                    xbmcData['movies'].append(item)
        if item is not None:
            cacheData['movies'].append(item)
        
    if traktData is None:
        
    _sync(xbmcData, traktData, cacheData)"""
        
        

##
# Sets
##
   
def getMovieLibrary():
    needSyncAtLeast(['movielibrary'])
    items = []
    for remoteId in movies:
        if not validRemoteId(remoteId): continue
        movie = movies[remoteId]
        if movie is None:
            continue
        items.append(movie)
    return items
def getShows():
    raise NotImplementedError()
def getShowEpisodes():
    raise NotImplementedError()
def getMovieWatchlist():
    needSyncAtLeast(['moviewatchlist'])
    watchlist = []
    for remoteId in movies:
        if not validRemoteId(remoteId): continue
        movie = movies[remoteId]
        if movie is None:
            continue
        if movie['_watchlistStatus'] == True:
            watchlist.append(movie)
    return watchlist    
def getShowWatchlist():
    needSyncAtLeast(['showwatchlist'])
    watchlist = []
    for remoteId in shows:
        if not validRemoteId(remoteId): continue
        show = shows[remoteId]
        if show is None:
            continue
        if show['_watchlistStatus'] == True:
            watchlist.append(show)
    return watchlist  
def getRecommendedMovies():
    needSyncAtLeast(['movierecommended'])
    items = []
    for remoteId in movies:
        if not validRemoteId(remoteId): continue
        movie = movies[remoteId]
        if movie is None:
            continue
        if movie['_recommendedStatus'] == True:
            items.append(movie)
    return items
def getTrendingMovies():
    traktItems = Trakt.moviesTrending();
    items = []
    for movie in traktItems:
        localMovie = Movie.fromTrakt(movie)
        items.append(localMovie)
    return items

def refreshSet(set, _structure=None, force=False):
    if force or checkTTL(set):
        if set in _refresh and _refresh[set] is not None:
            _refresh[set]()
            return True
        else:
            if _structure is None:
                _structure = _setStucture
            if set in _structure:
                complete = False
                for subSet in _structure[set]:
                    if refreshSet(subSet, _structure=_structure[set], force=force):
                        complete = True
                if complete:
                    updateSyncTimes([set])
                return complete
            else:
                for subSet in _structure:
                    refreshSet(set, _structure=_structure[subSet], force=force)
                if len(_structure.keys())==0:
                    Debug("[TraktCache] No method specified to refresh the set: "+str(set))
        return False
    else:
        return True

def refreshMovieLibrary():
    Debug("[TraktCache] Refreshing movie watchlist")
    traktSet = Movie.setFromTrakt('libraryStatus', Trakt.userLibraryMoviesCollection(username))
    diff = Movie.diffSet('libraryStatus', None, Movie, traktSet)
    TCQueue.add(diff)
    updateSyncTimes(['movielibrary'])
    
def refreshMovieWatchlist():
    Debug("[TraktCache] Refreshing movie watchlist")
    traktWatchlist = Movie.setFromTrakt('watchlistStatus', Trakt.userWatchlistMovies(username))
    diff = Movie.diffSet('watchlistStatus', None, Movie, traktWatchlist)
    TCQueue.add(diff)
    updateSyncTimes(['moviewatchlist'])
    
def refreshShowWatchlist():
    Debug("[TraktCache] Refreshing show watchlist")
    traktSet = Show.setFromTrakt('watchlistStatus', Trakt.userWatchlistShows(username))
    diff = Show.diffSet('watchlistStatus', None, Show, traktSet)
    TCQueue.add(diff)
    updateSyncTimes(['showwatchlist'])
        
def refreshEpisodeWatchlist():
    Debug("[TraktCache] Refreshing episode watchlist")
    traktSet = Episode.setFromTrakt('watchlistStatus', Trakt.userWatchlistEpisodes(username))
    diff = Episode.diffSet('watchlistStatus', None, Episode, traktSet)
    TCQueue.add(diff)
    updateSyncTimes(['episodewatchlist'])
    
def refreshRecommendedMovies():
    Debug("[TraktCache] Refreshing recommended movies")
    traktSet = Movie.setFromTrakt('recommendedStatus', Trakt.recommendationsMovies())
    diff = Movie.diffSet('recommendedStatus', None, Movie, traktSet)
    TCQueue.add(diff)
    updateSyncTimes(['movierecommended'])
    
def refreshRecommendedShows():
    Debug("[TraktCache] Refreshing recommended shows")
    traktSet = Movie.setFromTrakt('recommendedStatus', Trakt.recommendationsShows())
    diff = Show.diffSet('recommendedStatus', None, Show, traktSet)
    TCQueue.add(diff)
    updateSyncTimes(['showrecommended'])
    
_refresh = {}
_refresh['all'] = None
_refresh['library'] = None
_refresh['movieall'] = None
_refresh['movielibrary'] = refreshMovieLibrary
_refresh['episodelibrary'] = None
_refresh['moviewatchlist'] = refreshMovieWatchlist
_refresh['movierecommended'] = refreshRecommendedMovies
_refresh['movieseen'] = None
_refresh['showall'] = None
_refresh['showrecommended'] = refreshRecommendedShows
_refresh['showwatchlist'] = refreshShowWatchlist
_refresh['episodeall'] = None
_refresh['episodelibrary'] = None
_refresh['episodewatchlist'] = refreshEpisodeWatchlist
_refresh['episodeseen'] = None
