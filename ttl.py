from sqlobject import *
from utilities import Debug

class TTL(SQLObject):
	name = StringCol()
	time = DateTimeCol()