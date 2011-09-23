# -*- coding: utf-8 -*-
# 

import xbmc,xbmcaddon,xbmcgui
from utilities import *

__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

# read settings
__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

apikey = '48dfcb4813134da82152984e8c4f329bc8b8b46a'
username = __settings__.getSetting("username")
pwd = sha.new(__settings__.getSetting("password")).hexdigest()
debug = __settings__.getSetting( "debug" )

conn = httplib.HTTPConnection('api.trakt.tv')
headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}

class UnitTests():
    _tests = []
    # Run all tests
    
    @staticmethod
    def runAll():
        for i in range(0,len(UnitTests._tests)):
            run(i)

    @staticmethod
    def names():
        nameArray = []
        for i in range(0,len(UnitTests._tests)):
            nameArray.append(UnitTests._tests[i]['name'])
        return nameArray
    
    @staticmethod
    def count():
        return len(UnitTests._tests)
        
    @staticmethod
    def run(idx):
        Debug("[UnitTest] Testing: "+UnitTests._tests[idx]['name'])
        try:
            UnitTests._tests[idx]['method']()
        except AssertionError as ae:
            #Test failed
            return False
        return True
        
def getTrendingMoviesFromTraktTest():
    Debug("[UnitTest] Result: "+repr(getTrendingMoviesFromTrakt()))
    
def getMoviesFromXBMCTest():
    Debug("[UnitTest] Result: "+repr(getMoviesFromXBMC()))
    
UnitTests._tests.append({"name": "Get trending movies from trakt", "method": getTrendingMoviesFromTraktTest})
UnitTests._tests.append({"name": "Get movies from XBMC", "method": getMoviesFromXBMCTest})