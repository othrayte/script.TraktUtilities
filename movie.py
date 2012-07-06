# -*- coding: utf-8 -*-
#

from datetime import datetime

import xbmc,xbmcaddon

from sqlobject import *

from utilities import *
import trakt_cache
from trakt import Trakt
from ids import RemoteId, LocalId
from syncable import Syncable
from identifiable_object import IdentifiableObject
from tc_queue import TCQueue
from exc_types import *

__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

# Caches all information between the add-on and the web based trakt api
class Movie(IdentifiableObject, Syncable):    
    _title = UnicodeCol(default=None)
    _year = IntCol(default=None)
    _runtime = IntCol(default=None)
    _released = DateTimeCol(default=None)
    _tagline = UnicodeCol(default=None)
    _overview = UnicodeCol(default=None)
    _classification = StringCol(default=None)
    _playcount = IntCol(default=None)
    _rating = IntCol(default=None)
    _watchlistStatus = BoolCol(default=None)
    _recommendedStatus = BoolCol(default=None)
    _libraryStatus = BoolCol(default=None)
    _traktDbStatus = BoolCol(default=None)

    _poster = UnicodeCol(default=None)
    _fanart = UnicodeCol(default=None)

    _trailer = UnicodeCol(default=None)

    _lastUpdate = PickleCol(default={})


    _syncToXBMC = set(['_playcount'])
    _syncToTrakt = set(['_playcount', '_rating', '_watchlistStatus', '_libraryStatus'])
    _unsafeProperties = set(['_title',  '_year', '_runtime', '_released', '_tagline', '_overview', '_classification', '_playcount', '_rating', '_watchlistStatus',  '_recommendedStatus', '_libraryStatus', '_traktDbStatus', '_trailer', '_poster', '_fanart'])
            
    def __repr__(self):
        return "<"+repr(self['_title'])+" ("+str(self['_year'])+") - "+str(self['_remoteId'])+","+str(self['_libraryStatus'])+","+str(self['_poster'])+","+str(self['_runtime'])+","+repr(self['_tagline'])+">"
        
    def __str__(self):
        return unicode(self._title)+" ("+str(self._year)+")"
    
    def __getitem__(self, index):
        if index == "_title": return self._title
        if index == "_year": return self._year
        if index == "_runtime": return self._runtime
        if index == "_released": return self._released
        if index == "_tagline": return self._tagline
        if index == "_overview": return self._overview
        if index == "_classification": return self._classification
        if index == "_playcount": return self._playcount
        if index == "_rating": return self._rating
        if index == "_watchlistStatus": return self._watchlistStatus
        if index == "_recommendedStatus": return self._recommendedStatus
        if index == "_libraryStatus": return self._libraryStatus
        if index == "_traktDbStatus": return self._traktDbStatus
        if index == "_trailer": return self._trailer
        if index == "_poster": return self._poster
        if index == "_fanart": return self._fanart
    
    def __setitem__(self, index, value):
        if index == "_title": self._title = value
        if index == "_year": self._year = value
        if index == "_runtime": self._runtime = value
        if index == "_released": self._released = value
        if index == "_tagline": self._tagline = value
        if index == "_overview": self._overview = value
        if index == "_classification": self._classification = value
        if index == "_playcount": self._playcount = value
        if index == "_rating": self._rating = value
        if index == "_watchlistStatus": self._watchlistStatus = value
        if index == "_recommendedStatus": self._recommendedStatus = value
        if index == "_libraryStatus": self._libraryStatus = value
        if index == "_traktDbStatus": self._traktDbStatus = value
        if index == "_trailer": self._trailer = value
        if index == "_poster": self._poster = value
        if index == "_fanart": self._fanart = value

    def refresh(self, property = None):
        if property in ('_recommendedStatus'):
            refreshRecommendedMovies()
            return

        xbmcMovies = []
        for localId in self._localIds:
            movie = Movie.fromXbmc(XbmcVideoLibrary.getMovieDetails(localId.localid,['title', 'year', 'originaltitle', 'imdbnumber', 'playcount', 'lastplayed', 'runtime']))
            if movie is None:
               movie = {}
            xbmcMovies.append(movie)
        xbmcMovie = Movie.mergeListStatic(xbmcMovies)
        
        traktMovie = self.download()

        changes = self.diff(xbmcMovie, traktMovie)
        TCQueue.add([changes])
        trakt_cache.updateXbmc()
        trakt_cache.updateTrakt()
        
    @property
    def remoteId(self):
        """A unique identifier for the movie."""
        return self._remoteId
        
    @property
    def title(self):
        """The title of the movie."""
        self.checkExpire('_title')
        return self._title
        
    @property
    def year(self):
        """The year the movie was released."""
        self.checkExpire('_year')
        return self._year
        
    @property
    def runtime(self):
        """The number of minutes the movie runs for."""
        self.checkExpire('_runtime')
        return self._runtime
        
    @property
    def released(self):
        """The date the movie was released."""
        self.checkExpire('_released')
        return self._released
        
    @property
    def tagline(self):
        """A tag-line about the movie (like a catch phrase)."""
        self.checkExpire('_tagline')
        return self._tagline
        
    @property
    def overview(self):
        """An overview of the movie (like a plot)."""
        self.checkExpire('_overview')
        return self._overview
        
    @property
    def classification(self):
        """The content classification indicating the suitible audience."""
        self.checkExpire('_classification')
        return self._classification
        
    @property
    def trailer(self):
        """The movies trailer."""
        self.checkExpire('_trailer')
        return self._trailer
        
    @property
    def poster(self):
        """The movies poster image."""
        self.checkExpire('_poster')
        return self._poster
        
    @property
    def fanart(self):
        """The movies fanart image."""
        self.checkExpire('_fanart')
        return self._fanart
        
    def scrobble(self, progress):
        imdb = None
        for remoteId in _remoteIds:
            if remoteId.source == 'imdb':
                imdb = remoteId.remoteid
        return Trakt.movieScrobble(imdb, self._title, self._year, (self._runtime or 90), progress)
    def shout(self, text):
        raise NotImplementedError("This function has not been written")
    def watching(self, progress):
        imdb = None
        tmdb = None
        for remoteId in _remoteIds:
            if remoteId.source == 'imdb':
                imdb = remoteId.remoteid
            elif remoteId.source == 'tmdb':
                tmdb = remoteId.remoteid
        Trakt.movieWatching(imdb, self._title, self._year, (self._runtime or 90), progress, tmdb)
    @staticmethod
    def cancelWatching():
        Trakt.movieCancelWatching()
    def play(self):
        playMovieById(options = trakt_cache.getMovieLocalIds(self._remoteId))
    
    def Property(func):
        return property(**func()) 
    
    @property
    def rating(self):
        self.checkExpire('_rating')
        return self._rating
    @rating.setter
    def rating(self, value):
        trakt_cache.makeChanges({'movies': [{'remoteId': self._remoteId, 'subject': '_rating', 'value': value}]}, traktOnly = True)
        self.refresh()
        
    @property
    def playcount(self):
        """How many time the user has watched the movie."""
        self.checkExpire('_playcount')
        return self._playcount
    @playcount.setter
    def playcount(self, value):
        trakt_cache.makeChanges({'movies': [{'remoteId': self._remoteId, 'subject': '_playcount', 'value': value}]}, traktOnly = True)
        self.refresh()
        
    @property
    def libraryStatus(self):
        """Whether the movie is in the users library."""
        trakt_cache.needSyncAtLeast(['movielibrary'])
        return self._libraryStatus
        
    @property
    def watchingStatus(self):
        """Whether the user is currently watching the movie."""
        raise NotImplementedError("This function has not been written")
        
    @property
    def watchlistStatus(self):
        """Whether the movie is in the users watchlist."""
        trakt_cache.needSyncAtLeast(['moviewatchlist'])
        return self._watchlistStatus
    @watchlistStatus.setter
    def watchlistStatus(self, value):
        trakt_cache.makeChanges({'movies': [{'remoteId': self._remoteId, 'subject': '_watchlistStatus', 'value': value}]}, traktOnly = True)
        self.refresh()
        
    @property
    def recommendedStatus(self):
        """Whether the movie is recommended to the user by trakt."""
        trakt_cache.needSyncAtLeast(['movierecommended'])
        returnself._recommendedStatus
    
    def checkExpire(self, property):
        if self[str(property)] is None or (property in self._lastUpdate and self._lastUpdate[property]+timedelta(days=2) < time.time()):
            self.refresh(property)
    
    def download(self):
        movies = []
        for remoteId in self._remoteIds:
            if remoteId.source in ('imdb', 'tmdb'):
                try:
                    movies.append(Movie.fromTrakt(Trakt.movieSummary(remoteId.remoteid)))
                except TraktConnectionFailed:
                    break
                except TraktRequestFailed:
                    continue

        if len(movies) == 0:
            self._traktDbStatus = False
            return None

        return Movie.mergeListStatic(movies)
    
    def traktise(self):
        movie = {}
        movie['title'] = self._title
        movie['year'] = self._year
        movie['plays'] = self._playcount
        movie['in_watchlist'] = self._watchlistStatus
        movie['in_collection'] = self._libraryStatus
        movie['runtime'] = self._runtime
        
        movie['imdb_id'] = None
        movie['tmdb_id'] = None

        for remoteId in self._remoteIds:
            if remoteId.source == 'imdb':
                movie['imdb_id'] = remoteId.remoteid
            elif remoteId.source == 'tmdb':
                movie['tmdb_id'] = remoteId.remoteid

        return movie

    @staticmethod
    def fromTrakt(movie):
        if movie is None: return None
        local = {}
        local['_remoteIds'] = {}
        if 'imdb_id' in movie:
            local['_remoteIds']['imdb'] = movie['imdb_id']
        if 'tmdb_id' in movie:
            local['_remoteIds']['tmdb'] = movie['tmdb_id']

        local['_title'] = movie['title']
        local['_year'] = movie['year']
        if 'plays' in movie:
            local['_playcount'] = movie['plays']
        if 'in_watchlist' in movie:
            local['_watchlistStatus'] = movie['in_watchlist']
        if 'in_collection' in movie:
            local['_libraryStatus'] = movie['in_collection']
        if 'images' in movie and 'poster' in movie['images']:
            local['_poster'] = movie['images']['poster']
        if 'images' in movie and 'fanart' in movie['images']:
            local['_fanart'] = movie['images']['fanart']
        if 'runtime' in movie:
            local['_runtime'] = movie['runtime']
        if 'released' in movie:
            local['_released'] = datetime.fromtimestamp(movie['released'])
        if 'tagline' in movie:
            local['_tagline'] = movie['tagline']
        if 'overview' in movie:
            local['_overview'] = movie['overview']
        if 'certification' in movie:
            local['_classification'] = movie['certification']
        if 'trailer' in movie:
            local['_trailer'] = movie['trailer']
            
        return local
     
    @staticmethod
    def fromXbmc(movie):
        if movie is None: return None
        local = {}
        local['_remoteIds'] = {}
        local['_localIds'] = []
        if 'movieid' in movie:
            local['_localIds'].append(int(movie['movieid']))
        
        if 'imdbnumber' in movie and movie['imdbnumber'] is not None and movie['imdbnumber'].strip() != "":
            # Determine source
            if movie['imdbnumber'][:1] == 't':
                source = 'imdb'
            else:
                source = 'tmbd'
            local['_remoteIds'][source] = movie['imdbnumber']       

        if 'title' in movie:
            local['_title'] = movie['title']
        if 'year' in movie:
            local['_year'] = int(movie['year'])
        if 'playcount' in movie:
            local['_playcount'] = int(movie['playcount'])
        if 'runtime' in movie:
            local['_runtime'] = int(movie['runtime'])
        return local
    
    @staticmethod
    def updateTrakt(subject):
        if subject in Movie._syncToTrakt:
            changes = list(TCQueue.selectBy(dest='trakt', subject=subject))
            try:
                if subject == '_watchlistStatus':
                    Trakt.movieWatchlist([change.instance.traktise() for change in changes if change.value == True])
                    Trakt.movieUnwatchlist([change.instance.traktise() for change in changes if change.value == False])
                elif subject == '_playcount':
                    Trakt.movieSeen([change.instance.traktise() for change in changes if change.value > 0])
                    Trakt.movieUnseen([change.instance.traktise() for change in changes if change.value == 0])
                elif subject == '_libraryStatus':
                    Trakt.movieLibrary([change.instance.traktise() for change in changes if change.value == True])
                    Trakt.movieUnlibrary([change.instance.traktise() for change in changes if change.value == False])
                elif subject == '_rating':
                    Trakt.rateMovies(map(lambda change: change.instance.traktise(), changes))
                else:
                    raise NotImplementedError("This type, '"+subject+"', can't yet be synced back to trakt, maybe you could fix this.")
            except TraktRequestFailed:
                Debug("[Movie] Failed trakt.tv request prevented sending of info to trakt, this info will be resent next time: ")
        # Succeeded or ignored pass to cache
        changes = TCQueue.selectBy(dest='trakt', subject=subject).lazyColumns(True) # Don't need to get al the info out again
        for change in changes:
            change.dest = 'cache'

    @staticmethod
    def updateCache(subject):
        if subject in Movie._unsafeProperties:
            changes = list(TCQueue.selectBy(dest='cache', subject=subject))
            for change in changes:
                change.instance[subject] = change.value
                if change.soft == False:
                    change.instance._lastUpdate[subject] = change.time
        # Remove all, including any ones that could not be implemented
        TCQueue.deleteBy(dest='cache', subject=subject)

    @staticmethod
    def updateXBMC(subject):
        changes = TCQueue.selectBy(dest='trakt', subject=subject)
        if subject in Movie._syncToXBMC:
            for change in changes:
                succeeded = True
                for id in change.instance._localIds:
                    if subject == 'playcount':
                        if setXBMCMoviePlaycount(id.localid, change.value) is None:
                            succeeded = False# failed
                if succeeded:
                    # Succeeded pass to cache
                    changes = changes.lazyColumns(True) # Don't need to get all the info out again
                    for change in changes:
                        change.dest = 'cache'
        else:
            # Ignored pass to cache
            changes = changes.lazyColumns(True) # Don't need to get all the info out again
            for change in changes:
                change.dest = 'cache'

    @staticmethod
    def evolveId(idString):
        if idString.find('tt') == 0:
            return str("imdb="+idString.strip())
        else:
            return str("tmdb="+idString.strip())
    
    @staticmethod
    def devolveId(idString):
        #Debug("[Movie] Devolving id: "+str(idString))
        if idString.find('imdb=tt') == 0:
            return idString[5:]
        elif idString.find('imdb=') == 0:
            return "tt"+idString[5:]
        elif idString.find('tmbd=') == 0:
            return idString[5:]
