from sqlobject import *

class TTL(SQLObject):
	name = StringCol()
	time = DateTimeCol()