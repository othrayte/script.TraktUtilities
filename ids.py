from sqlobject import *
from sqlobject.inheritance import InheritableSQLObject

import movie
from show import Show
from episode import Episode

class RemoteId(InheritableSQLObject):
	source = StringCol()
	remoteid = StringCol()

class RemoteMovieId(RemoteId):
	movie = ForeignKey('Movie')

"""class RemoteShowId(RemoteId):
	show = ForeignKey('Show')

class RemoteEpisodeId(RemoteId):
	episode = ForeignKey('Episode')"""
		
class LocalId(InheritableSQLObject):
	localid = IntCol()

class LocalMovieId(LocalId):
	movie = ForeignKey('Movie')

"""class LocalShowId(LocalId):
	show = ForeignKey('Show')

class LocalEpisodeId(LocalId):
	episode = ForeignKey('Episode')"""