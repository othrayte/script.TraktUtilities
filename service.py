# -*- coding: utf-8 -*-
# 

import xbmc,xbmcaddon,xbmcgui

from utilities import *
from notification_service import NotificationService
from scrobbler import Scrobbler
import trakt_cache
import time
from async_tools import *

__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

Debug("service: " + __settings__.getAddonInfo("id") + " - version: " + __settings__.getAddonInfo("version"))

cacheDirectory = "special://profile/addon_data/script.TraktUtilities/"


# Initialise all of the background services    
def autostart():
    try:
        # Initialise the cache
        trakt_cache.init(os.path.join(cacheDirectory,"trakt_cache"))
            
        # Initialise the scrobbler
        global scrobbler
        scrobbler = Scrobbler()
        scrobbler.start()
        
        # Initialise the notification handler
        notificationThread = NotificationService()
        notificationThread.start()

        # Trigger update checks for the cache
        trakt_cache.trigger()
        
        tuThreads.join()
    except:
        e = sys.exc_info()
        tuThreads.finishUp()
        try:
            tuThreads.join()
        except AsyncCloseRequest:
            pass
        Debug("[Service] Cleaning up db")
        try:
            trakt_cache.close()
        except:
            pass
        Debug("[Service] Dieing");
        raise e[1], None, e[2]
    Debug("[Service] Cleaning up db")
    trakt_cache.close()
    Debug("[Service] Closing");
    
if __name__ == "__main__" :
    autostart()
