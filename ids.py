from sqlobject import *

class RemoteId(SQLObject):
	source = StringCol()
	remoteid = StringCol()
	instance = ForeignKey('IdentifiableObject')


class LocalId(SQLObject):
	type = StringCol()
	localid = IntCol()
	instance = ForeignKey('IdentifiableObject')