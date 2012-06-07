from sqlobject import *
from sqlobject.inheritance import *

class IdentifiableObject(InheritableSQLObject):
    _remoteIds = MultipleJoin('RemoteId', joinColumn='instance_id')
    _localIds = MultipleJoin('LocalId', joinColumn='instance_id')