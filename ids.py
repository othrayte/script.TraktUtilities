from sqlobject import *
from sqlobject.inheritance import InheritableSQLObject

class RemoteId(InheritableSQLObject):
	source = StringCol()
	remoteid = StringCol()

class LocalId(InheritableSQLObject):
	localid = IntCol()

class RemoteMovieId(RemoteId):
	movie = ForeignKey('Movie')
	def get():
		return movie

class LocalMovieId(LocalId):
	movie = ForeignKey('Movie')
	def get():
		return movie

class RemoteShowId(RemoteId):
	show = ForeignKey('Show')
	def get():
		return show
		
class LocalShowId(LocalId):
	show = ForeignKey('Show')
	def get():
		return show

class RemoteEpisodeId(RemoteId):
	episode = ForeignKey('Episode')
	def get():
		return episode

class LocalEpisodeId(LocalId):
	episode = ForeignKey('Episode')
	def get():
		return episode