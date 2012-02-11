# -*- coding: utf-8 -*-
# 

import xbmc,xbmcaddon
from utilities import *
import trakt_cache
from trakt import Trakt
from sqlobject import *
from ids import RemoteMovieId, LocalMovieId

__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

# Caches all information between the add-on and the web based trakt api
class Movie(SQLObject):
    _remoteIds = MultipleJoin('RemoteMovieId')
    _localIds = MultipleJoin('LocalMovieId')
    
    _title = StringCol(default=None)
    _year = IntCol(default=None)
    _runtime = IntCol(default=None)
    _released = DateTimeCol(default=None)
    _tagline = StringCol(default=None)
    _overview = StringCol(default=None)
    _classification = StringCol(default=None)
    _playcount = IntCol(default=None)
    _rating = IntCol(default=None)
    _watchlistStatus = BoolCol(default=None)
    _recommendedStatus = BoolCol(default=None)
    _libraryStatus = BoolCol(default=None)
    _traktDbStatus = BoolCol(default=None)

    _bestBefore = PickleCol(default={})

    __unsafeProperties = ('_title',  '_year', '_runtime', '_released', '_tagline', '_overview', '_classification', '_playcount', '_rating', '_watchlistStatus',  '_recommendedStatus', '_libraryStatus', '_traktDbStatus', '_trailer', '_poster', '_fanart')
            
    def __repr__(self):
        return "<"+repr(self._title)+" ("+str(self._year)+") - "+str(self._remoteId)+","+str(self._libraryStatus)+","+str(self._poster)+","+str(self._runtime)+","+repr(self._tagline)+">"
        
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
    
    def __iter__(self):
        for key in __unsafeProperties:
            yield key

    def __contains__(self, item):
        return item in __unsafeProperties
    
    def keys():
        return __unsafeProperties

    def refresh(self, property = None):
        if property in ('recommendedStatus'):
            refreshRecommendedMovies()
            return

        xbmcMovies = []
        for localId in _localIds:
            movie = Movie.fromXbmc(getMovieDetailsFromXbmc(localId,['title', 'year', 'originaltitle', 'imdbnumber', 'playcount', 'lastplayed', 'runtime']))
            if movie is None:
               movie = {}
            xbmcMovies.append(movie)
        xbmcMovie = Movie.mergeListStatic(xbmcMovies)
        
        traktMovie = download()

        changeVectors = compare(xbmcMovie, traktMovie)
    
    #Merging object data
    @staticmethod
    def mergeListStatic(list):
        movie = {}
        for item in list:
            mergeStatic(movie, item)
        return movie
    
    @staticmethod
    def mergeStatic(a, b):
        out = a
        for key in b.keys():
            if key in out:
                if key in ('rating', 'playcount', 'remoteIds', 'localIds'):
                    if key == 'rating':
                        out['rating'] = max(a['rating'], b['rating'])
                    elif key == 'playcount':
                        out['playcount'] = max(a['playcount'], b['playcount'])
                    elif key == 'remoteIds':
                        providers = b[key].keys()
                        for provider in providers:
                            if provider not in a[key] or a[key][provider] <> b[key][provider]:
                                a[key][provider] = b[key][provider]
                    elif key == 'localIds':
                        for id in b[key]:
                            if id not in a[key]:
                                a[key].append(id)

                else:
                    pass #conflict
            else:
                out[key] = b[key]
    return out
    
    #Merging objects
    def __ior__(self, other):
        for key in other.keys():
            if key in self:
                if key in ('_rating', '_playcount'):
                    out[key] = max(a[key], b[key])
                elif key == '_remoteIds':
                    idsS = self[key]
                    sources = {}
                    for id in idsS:
                        sources[id.source] = id
                    idsO = other[key]
                    for id in idsO:
                        if id.source not in sources.keys() or id.remoteId <> sources[id.source].remoteId:
                            id.movie = this
                        else:
                            id.destroySelf()
                elif key == '_localIds':
                    idsS = self[key]
                    ids = []
                    for id in idsS:
                        ids.append(id.localId)
                    idsO = other[key]
                    for id in idsO:
                        if id.localId not in ids.keys():
                            id.movie = this
                        else:
                            id.destroySelf()


                else:
                    pass #conflict
            else:
                self[key] = other[key]
        other.destroySelf()

    #Enumerate diff
    def __xor__(self, other):
        for key in self.keys():
            if self[key] <> other

# if nothing to do (externals unknown or all same)
    #next
# if new data (cache unknown)
    # if soft
        #next
    # else
        # if l unknown
# if simple (not all diff)
# All diff
"""
Three way compare logic
    /  ~
??? -  -
??1 <~ -
?1? -  -
?11 <  -
?12 <  <~
1?? >~ -
1?1 >< -
1?2 ?  -
11? >  -
111 -  -
112 <  ?
12? >  >~
121 >< ><
122 >  ?
123 ?  ?
"""

    def reread(self):
        newer = trakt_cache.getMovie(self._remoteId)
        if newer is None:
            return False
            
        self._title = newer._title
        self._year = newer._year
        self._runtime = newer._runtime
        self._released = newer._released
        self._tagline = newer._tagline
        self._overview = newer._overview
        self._classification = newer._classification
        self._playcount = newer._playcount
        self._rating = newer._rating
        self._watchlistStatus = newer._watchlistStatus
        self._recommendedStatus = newer._recommendedStatus
        self._libraryStatus = newer._libraryStatus
        self._traktDbStatus = newer._traktDbStatus
        
        self._trailer = newer._trailer
        
        self._poster = newer._poster
        self._fanart = newer._fanart
        
        self._bestBefore = newer._bestBefore
        self._static = newer._static
        
        return True
        
    @property
    def remoteId(self):
        """A unique identifier for the movie."""
        return self._remoteId
        
    @property
    def title(self):
        """The title of the movie."""
        self.checkExpire('title')
        return self._title
        
    @property
    def year(self):
        """The year the movie was released."""
        self.checkExpire('year')
        return self._year
        
    @property
    def runtime(self):
        """The number of minutes the movie runs for."""
        self.checkExpire('runtime')
        return self._runtime
        
    @property
    def released(self):
        """The date the movie was released."""
        self.checkExpire('released')
        return self._released
        
    @property
    def tagline(self):
        """A tag-line about the movie (like a catch phrase)."""
        self.checkExpire('tagline')
        return self._tagline
        
    @property
    def overview(self):
        """An overview of the movie (like a plot)."""
        self.checkExpire('overview')
        return self._overview
        
    @property
    def classification(self):
        """The content classification indicating the suitible audience."""
        self.checkExpire('classification')
        return self._classification
        
    @property
    def trailer(self):
        """The movies trailer."""
        self.checkExpire('trailer')
        return self._trailer
        
    @property
    def poster(self):
        """The movies poster image."""
        self.checkExpire('poster')
        return self._poster
        
    @property
    def fanart(self):
        """The movies fanart image."""
        self.checkExpire('fanart')
        return self._fanart
        
    def scrobble(self, progress):
        scrobbleMovieOnTrakt(self.traktise(), progress)
    def shout(self, text):
        raise NotImplementedError("This function has not been written")
    def watching(self, progress):
        watchingMovieOnTrakt(self.traktise(), progress)
    @staticmethod
    def cancelWatching():
        cancelWatchingMovieOnTrakt()
    def play(self):
        playMovieById(options = trakt_cache.getMovieLocalIds(self._remoteId))
    
    def Property(func):
        return property(**func()) 
    
    @property
    def rating(self):
        self.checkExpire('rating')
        return self._rating
    @rating.setter
    def rating(self, value):
        trakt_cache.makeChanges({'movies': [{'remoteId': self._remoteId, 'subject': 'rating', 'value': value}]}, traktOnly = True)
        self.refresh()
        
    @property
    def playcount(self):
        """How many time the user has watched the movie."""
        self.checkExpire('playcount')
        return self._playcount
    @playcount.setter
    def playcount(self, value):
        trakt_cache.makeChanges({'movies': [{'remoteId': self._remoteId, 'subject': 'playcount', 'value': value}]}, traktOnly = True)
        self.refresh()
        
    @property
    def libraryStatus(self):
        """Whether the movie is in the users library."""
        if not self._static: trakt_cache.needSyncAtLeast(['movielibrary'])
        return self._libraryStatus
        
    @property
    def watchingStatus(self):
        """Whether the user is currently watching the movie."""
        raise NotImplementedError("This function has not been written")
        
    @property
    def watchlistStatus(self):
        """Whether the movie is in the users watchlist."""
        if not self._static: trakt_cache.needSyncAtLeast(['moviewatchlist'])
        return self._watchlistStatus
    @watchlistStatus.setter
    def watchlistStatus(self, value):
        trakt_cache.makeChanges({'movies': [{'remoteId': self._remoteId, 'subject': 'watchlistStatus', 'value': value}]}, traktOnly = True)
        self.refresh()
        
    @property
    def recommendedStatus(self):
        """Whether the movie is recommended to the user by trakt."""
        if not self._static: trakt_cache.needSyncAtLeast(['movierecommended'])
        returnself._recommendedStatus
    
    def checkExpire(self, property):
        if self._static:
            return
        if property not in self._bestBefore or self['_'+str(property)] is None or self._bestBefore[property] < time.time():
            self.refresh(property)
        
    @staticmethod
    def download(remoteId):
        Debug("[Movie] Downloading info for "+str(Movie.devolveId(remoteId)))
        responce = Trakt.movieSummary(Movie.devolveId(remoteId), returnStatus=True)
        if responce is not None and 'status' in responce and responce['status'] == 'failure':
            if 'error' in responce and responce['error'] == 'movie not found':
                movie = Movie(remoteId)
                movie._traktDbStatus = False
                return movie
        return Movie.fromTrakt(responce)
    
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
        if str(self._remoteId).find('imdb=') == 0:
            movie['imdb_id'] = self._remoteId[5:]
        if str(self._remoteId).find('tmdb=') == 0:
            movie['tmdb_id'] = self._remoteId[5:]
        return movie
        
    @staticmethod
    def fromTrakt(movie, static = True):
        if movie is None: return None
        local = {}
        local['remoteIds'] = []
        if 'imdb_id' in movie:
            local['remoteIds'].append({'imdb': movie['imdb_id']})
        if 'tmdb_id' in movie:
            local['remoteIds'].append({'tmdb': movie['tmdb_id']})

        local['title'] = movie['title']
        local['year'] = movie['year']
        if 'plays' in movie:
            local['playcount'] = movie['plays']
        if 'in_watchlist' in movie:
            local['watchlistStatus'] = movie['in_watchlist']
        if 'in_collection' in movie:
            local['libraryStatus'] = movie['in_collection']
        if 'images' in movie and 'poster' in movie['images']:
            local['poster'] = movie['images']['poster']
        if 'images' in movie and 'fanart' in movie['images']:
            local['fanart'] = movie['images']['fanart']
        if 'runtime' in movie:
            local['runtime'] = movie['runtime']
        if 'released' in movie:
            local['released'] = movie['released']
        if 'tagline' in movie:
            local['tagline'] = movie['tagline']
        if 'overview' in movie:
            local['overview'] = movie['overview']
        if 'certification' in movie:
            local['classification'] = movie['certification']
        if 'trailer' in movie:
            local['trailer'] = movie['trailer']
            
        return local
     
    @staticmethod
    def fromXbmc(movie, static = True):
        if movie is None: return None
        #Debug("[Movie] Creating from: "+str(movie))
        if 'imdbnumber' not in movie or movie['imdbnumber'] is None or movie['imdbnumber'].strip() == "":
            remoteId = trakt_cache.getMovieRemoteId(movie['movieid'])
            if remoteId is not None:
                local = Movie(remoteId, static)
            else:
                imdb_id = searchGoogleForImdbId(unicode(movie['title'])+"+"+unicode(movie['year']))
                if imdb_id is None or imdb_id == "":
                    traktMovie = searchTraktForMovie(movie['title'], movie['year'])
                    if traktMovie is None:
                         Debug("[Movie] Unable to find movie '"+unicode(movie['title'])+"' ["+unicode(movie['year'])+"]")
                    else:
                        if 'imdb_id' in traktMovie and traktMovie['imdb_id'] <> "":
                            local = Movie("imdb="+traktMovie['imdb_id'], static)
                        elif 'tmdb_id' in traktMovie and traktMovie['tmdb_id'] <> "":
                            local = Movie("tmdb="+traktMovie['tmdb_id'], static)
                        else:
                            return None
                    return None
                else:
                    local = Movie("imdb="+imdb_id, static)
        else:
            local = Movie(Movie.evolveId(movie['imdbnumber']), static)
        trakt_cache.relateMovieId(movie['movieid'], local._remoteId)
        if local._remoteId == 'imdb=' or local._remoteId == 'tmdb=':
            Debug("[Movie] Fail tried to use blank remote id for "+repr(movie))
            return None
        local._title = movie['title']
        local._year = movie['year']
        local._playcount = movie['playcount']
        local._runtime = movie['runtime']
        return local
    
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
        