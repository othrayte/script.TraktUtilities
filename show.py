# -*- coding: utf-8 -*-
# 

import xbmc,xbmcaddon

from sqlobject import *

from utilities import Debug
import trakt_cache
from trakt import Trakt
from ids import RemoteId, LocalId
from syncable import Syncable
from identifiable_object import IdentifiableObject
from tc_queue import TCQueue

__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

# Caches all information between the add-on and the web based trakt api
class Show(IdentifiableObject, Syncable):
    _title = StringCol(default=None)
    _year = IntCol(default=None)

    _episodes = MultipleJoin('Episode', joinColumn='show_id')

    _firstAired = IntCol(default=None)
    _country = StringCol(default=None)
    _overview = StringCol(default=None)
    _runtime = IntCol(default=None)
    _network = StringCol(default=None)
    _airDay = StringCol(default=None)
    _airTime = IntCol(default=None)
    _classification = StringCol(default=None)
    _rating = IntCol(default=None)
    _watchlistStatus = BoolCol(default=None)
    _recommendedStatus = BoolCol(default=None)
    _traktDbStatus = BoolCol(default=None)
    
    _poster = StringCol(default=None)
    _fanart = StringCol(default=None)
    _banner = StringCol(default=None)
    
    _lastUpdate = PickleCol(default={})

    _syncToXBMC = set([])
    _syncToTrakt = set(['_rating', '_watchlistStatus'])
    _unsafeProperties = set(['_title',  '_year', '_firstAired', '_country', '_overview', '_runtime', '_network', '_airDay', '_airTime', '_classification', '_rating', '_watchlistStatus',  '_recommendedStatus', '_traktDbStatus', '_trailer', '_poster', '_fanart', '_banner'])
    
    
    def __repr__(self):
        return "<"+repr(self['_title'])+" ("+str(self['_year'])+") - "+str(self['_remoteId'])+","+str(self['_poster'])+","+str(self['_runtime'])+">"
        
    def __str__(self):
        return unicode(self['_title'])+" ("+str(self['_year'])+")"
        
    def __getitem__(self, index):
        if index == "_title": return self._title
        if index == "_year": return self._year
        if index == "_firstAired": return self._firstAired
        if index == "_country": return self._country
        if index == "_overview": return self._overview
        if index == "_runtime": return self._runtime
        if index == "_network": return self._network
        if index == "_airDay": return self._airDay
        if index == "_airTime": return self._airTime
        if index == "_classification": return self._classification
        if index == "_rating": return self._rating
        if index == "_watchlistStatus": return self._watchlistStatus
        if index == "_recommendedStatus": return self._recommendedStatus
        if index == "_poster": return self._poster
        if index == "_fanart": return self._fanart
        if index == "_episodes": return self._episodes
    
    def __setitem__(self, index, value):
        if index == "_title": self._title = value
        if index == "_year": self._year = value
        if index == "_firstAired": self._firstAired = value
        if index == "_country": self._country = value
        if index == "_overview": self._overview = value
        if index == "_runtime": self._runtime = value
        if index == "_network": self._network = value
        if index == "_airDay": self._airDay = value
        if index == "_airTime": self._airTime = value
        if index == "_classification": self._classification = value
        if index == "_rating": self._rating = value
        if index == "_watchlistStatus": self._watchlistStatus = value
        if index == "_recommendedStatus": self._recommendedStatus = value
        if index == "_poster": self._poster = value
        if index == "_fanart": self._fanart = value
        if index == "_episodes": self._episodes = value
    
    def save(self):
        trakt_cache.saveShow(self)
    
    def refresh(self, property = None):
        if not self._static:
            trakt_cache.refreshShow(self._remoteId, property)
            self.reread()
        
    def reread(self):
        newer = trakt_cache.getShow(self._remoteId)
        if newer is None:
            return False
        
        self._title = newer._title
        self._year = newer._year
        self._firstAired = newer._firstAired
        self._country = newer._country
        self._overview = newer._overview
        self._runtime = newer._runtime
        self._network = newer._network
        self._airDay = newer._airDay
        self._airTime = newer._airTime
        self._classification = newer._classification
        self._rating = newer._rating
        self._watchlistStatus = newer._watchlistStatus
        self._recommendedStatus = newer._recommendedStatus
        self._traktDbStatus = newer._traktDbStatus
        
        self._poster = newer._poster
        self._fanart = newer._fanart
        
        self._episodes = newer._episodes
        
        self._bestBefore = newer._bestBefore
        self._static = newer._static
        
        return True
            
    @property
    def remoteId(self):
        """A unique identifier for the show."""
        return self._remoteId
        
    @property
    def title(self):
        """The title of the show."""
        self.checkExpire('title')
        return self._title
        
    @property
    def year(self):
        """The year the show was first aired."""
        self.checkExpire('year')
        return self._year
        
    @property
    def firstAired(self):
        """The date the show was first aired."""
        self.checkExpire('firstAired')
        return self._firstAired
        
    @property
    def country(self):
        """The country in which the show was first aired."""
        self.checkExpire('country')
        return self._country
        
    @property
    def overview(self):
        """An overview of the show (like a plot)."""
        self.checkExpire('overview')
        return self._overview
        
    @property
    def runtime(self):
        """The standard runtime of the show."""
        self.checkExpire('runtime')
        return self._runtime
        
    @property
    def network(self):
        """The TV network the show first aired on."""
        self.checkExpire('network')
        return self._network
        
    @property
    def airDay(self):
        """The day of the week that the show first airs."""
        self.checkExpire('airDay')
        return self._airDay
        
    @property
    def airTime(self):
        """The time of day that the show first airs."""
        self.checkExpire('airTime')
        return self._airTime
        
    @property
    def classification(self):
        """The content classification indicating the suitible audience."""
        self.checkExpire('classification')
        return self._classification
        
    @property
    def poster(self):
        """The shows poster image."""
        self.checkExpire('poster')
        return self._poster
        
    @property
    def fanart(self):
        """The shows fanart image."""
        self.checkExpire('fanart')
        return self._fanart
        
    def episodes(self, seasonFilter=None, episodeFilter=None):
        matches = []
        for season in self._episodes.keys:
            if season == seasonFilter or seasonFilter is None:
                for episode in self._episodes[season].keys:
                    if episode == episodeFilter or episodeFilter is None:
                        matches.append(getEpisode(self._remoteID, season+'x'+episode))
        return matches
        
    def shout(self, text):
        raise NotImplementedError("This function has not been written")
    def watching(self, progress):
        raise NotImplementedError("This function has not been written")
    @staticmethod
    def cancelWatching():
        raise NotImplementedError("This function has not been written")
    def playNext(self):
        # Determine which is the next episode and play it
        xbmcgui.Dialog().ok("Trakt Utilities", "comming soon")
    
    def Property(func):
        return property(**func()) 
    
    @property
    def rating(self):
        self.checkExpire('rating')
        return self._rating
    @rating.setter
    def rating(self, value):
        trakt_cache.makeChanges({'shows': [{'remoteId': self._remoteId, 'subject': 'rating', 'value': value}]}, traktOnly = True)
        self.refresh()
        
    @property
    def watchingStatus(self):
        """Whether the user is currently watching the show."""
        raise NotImplementedError("This function has not been written")
        
    @property
    def watchlistStatus(self):
        """Whether the show is in the users watchlist."""
        if not self._static: trakt_cache.needSyncAtLeast(['showwatchlist'])
        return self._watchlistStatus
    @watchlistStatus.setter
    def watchlistStatus(self, value):
        trakt_cache.makeChanges({'shows': [{'remoteId': self._remoteId, 'subject': 'watchlistStatus', 'value': value}]}, traktOnly = True)
        self.refresh()
        
    @property
    def recommendedStatus(self):
        """Whether the show is recommended to the user by trakt."""
        if not self._static: trakt_cache.needSyncAtLeast(['showrecommended'])
        returnself._recommendedStatus
    
    def checkExpire(self, property):
        if self._static:
            return
        if property not in self._bestBefore or self['_'+str(property)] is None or self._bestBefore[property] < time.time():
            self.refresh(property)
        
    @staticmethod
    def download(remoteId):
        Debug("[Show] Downloading info for "+str(Show.devolveId(remoteId)))
        local = Trakt.showSummary(Show.devolveId(remoteId))
        if local is None:
            show = Show(remoteId)
            show._traktDbStatus = False
            return movie
        return Show.fromTrakt(local)
        
    def traktise(self):
        show = {}
        show['title'] = self._title
        show['year'] = self._year
        show['in_watchlist'] = self._watchlistStatus
        show['in_collection'] = self._libraryStatus
        
        show['imdb_id'] = None
        show['tvdb_id'] = None
        if str(self._remoteId).find('tvbd=') == 0:
            show['tvdb_id'] = self._remoteId[5:]
        if str(self._remoteId).find('imbd=') == 0:
            show['imdb_id'] = self._remoteId[5:]
        return show
        
    @staticmethod
    def fromTrakt(show, static = True):
        if show is None: return None
        local = {}
        local['_remoteIds'] = {}
        if 'tvdb_id' in show:
            local['_remoteIds']['tvdb'] = show['tvdb_id']
        if 'imdb_id' in show:
            local['_remoteIds']['imdb'] = show['imdb_id']

        local['title'] = show['title']
        local['year'] = show['year']
        if 'in_watchlist' in show:
            local['watchlistStatus'] = show['in_watchlist']
        if 'images' in show and 'poster' in show['images']:
            local['poster'] = show['images']['poster']
        if 'images' in show and 'fanart' in show['images']:
            local['fanart'] = show['images']['fanart']
        if 'first_aired' in show:
            local['firstAired'] = show['first_aired']
        if 'coutnry' in show:
            local['coutnry'] = show['coutnry']
        if 'network' in show:
            local['network'] = show['network']
        if 'runtime' in show:
            local['runtime'] = show['runtime']
        if 'air_day' in show:
            local['airDay'] = show['air_day']
        if 'air_time' in show:
            local['airTime'] = show['air_time']
        if 'tagline' in show:
            local['tagline'] = show['tagline']
        if 'overview' in show:
            local['overview'] = show['overview']
        if 'certification' in show:
            local['classification'] = show['certification']
        return locals
        
    @staticmethod
    def fromXbmc(show, static = True):
        if show is None: return None
        if 'imdbnumber' not in show or show['imdbnumber'] is None or show['imdbnumber'].strip() == "":
            Debug("[~] "+repr(show))
            remoteId = trakt_cache.getShowRemoteId(show['showid'])
            if remoteId is not None:
                local = Show(remoteId, static)
            else:
                tvdb_id = searchGoogleForTvdbId(unicode(Show['title'])+"+"+unicode(Show['year']))
                if tvdb_id is None or tvdb_id == "":
                    traktShow = searchTraktForShow(show['title'], show['year'])
                    if traktShow is None:
                         Debug("[Show] Unable to find show '"+unicode(show['title'])+"' ["+unicode(show['year'])+"]")
                    else:
                        if 'tvdb_id' in traktMovie and traktMovie['tvdb_id'] <> "":
                            local = Show("tvdb="+traktMovie['tvdb_id'], static)
                        elif 'imdb_id' in traktMovie and traktMovie['imdb_id'] <> "":
                            local = Show("imdb="+traktMovie['imdb_id'], static)
                        else:
                            return None
                    return None
                else:
                    local = Show("tvdb="+tvdb_id, static)
        else:
            local = Show(Show.evolveId(show['imdbnumber']), static)
        trakt_cache.relateShowId(show['tvshowid'], local._remoteId)
        if local._remoteId == 'tvdb=' or local._remoteId == 'imdb=':
            Debug("[Show] Fail tried to use blank remote id for "+repr(show))
            return None
        if 'title' in show: local._title = show['title']
        if 'year' in show: local._year = show['year']
        if 'runtime' in show: local._runtime = show['runtime']
        return local
    
    @staticmethod
    def updateTrakt(subject):
        changes = list(TCQueue.selectBy(dest='trakt', subject=subject))
        if subject in Show._syncToTrakt:
            try:
                if subject == 'watchlistStatus':
                    Trakt.showWatchlist([change.instance.traktise() for change in changes if change.value == True])
                    Trakt.showUnwatchlist([change.instance.traktise() for change in changes if change.value == False])
                elif subject == 'rating':
                    Trakt.rateShows(map(lambda change: change.instance.traktise(), changes))
                else:
                    raise NotImplementedError("This type, '"+subject+"', can't yet be synced back to trakt, maybe you could fix this.")
            except TraktRequestFailed:
                mutate(TraktUpdateFailed, "Failed trakt.tv request prevented sending of info to trakt, this info will be resent next time: ")
        # Succeeded or ignored pass to cache
        changes = changes.lazyColumns(True) # Don't need to get al the info out again
        for change in changes:
            change.dest = 'cache'

    @staticmethod
    def updateCache(subject):
        if subject in Show._unsafeProperties:
            changes = list(TCQueue.selectBy(dest='cache', subject=subject))
            for change in changes:
                change.instance['_'+subject] = change.value
                if change.soft == False:
                    change.instance._lastUpdate[subject] = change.time
        # Remove all, including any ones that could not be implemented
        TCQueue.deleteBy(dest='cache', subject=subject)

    @staticmethod
    def updateXBMC(subject):
        changes = TCQueue.selectBy(dest='trakt', subject=subject)
        if subject in Show._syncToXBMC:
            for change in changes:
                succeeded = True
                for id in change.instance._localIds:
                    # At some point we will do some updating here
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
            return str("tvdb="+idString.strip())
    
    @staticmethod
    def devolveId(idString):
        if idString.find('imdb=tt') == 0:
            return idString[5:]
        elif idString.find('imdb=') == 0:
            return "tt"+idString[5:]
        elif idString.find('tvdb=') == 0:
            return idString[5:]