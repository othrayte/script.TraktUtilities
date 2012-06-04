from sqlobject import *
from sqlobject.inheritance import *

class IdentifiableObject(InheritableSQLObject):
    _remoteIds = MultipleJoin('RemoteMovieId')
    _localIds = MultipleJoin('LocalMovieId')