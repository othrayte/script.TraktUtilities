# -*- coding: utf-8 -*-
# 

__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

##
# Exceptions
##

#TODO: Separate generic, trakt and TU exceptions

# When called from a caught exception this will mutate the typr of the exception and append the str() of the passed exception type instance
def mutate(new, value):
    import sys
    inf = sys.exc_info()
    raise new((value,inf[1])), None, inf[2]

##
# Syncronisationss
##

class TUSyncFailed(Exception):
    def __init__(self, value=""):
        self.value = value
    def __str__(self):
        return repr(self.value)

##
# Trakt.tv requests
##

class TraktError(Exception):
    def __init__(self, value=""):
        self.value = value
    def __str__(self):
        return repr(self.value)

class TraktRequestInvalid(Exception):
    def __init__(self, value=""):
        self.value = value
    def __str__(self):
        return repr(self.value)

class TraktRequestFailed(TraktError):
    def __init__(self, value=""):
        self.value = value
    def __str__(self):
        return repr(self.value)

class TraktConnectionFailed(TraktRequestFailed):
    def __init__(self, value=""):
        self.value = value
    def __str__(self):
        return repr(self.value)