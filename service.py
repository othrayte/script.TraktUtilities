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

Debug("[Service] " + __settings__.getAddonInfo("id") + " - version: " + __settings__.getAddonInfo("version"))

cacheDirectory = "special://profile/addon_data/script.TraktUtilities/"


# Initialise all of the background services    
def autostart():

    checkSettings()

    try:
        # Initialise the cache
        trakt_cache.init(os.path.join(cacheDirectory,"trakt_cache"))
            
        # Initialise the scrobbler
        scrobbler = Scrobbler()
        scrobbler.start().ignore()

        # Initialise the notification handler
        notificationService = NotificationService()
        notificationService.start().ignore()
        notificationService.scrobbler = scrobbler

        # Trigger update checks for the cache
        trakt_cache.trigger()
        
        tuThreads.join()
    except AsyncCloseRequest:
        Debug("[Service] Somewhere threads were asked to finish")
        Debug("[Service] Waiting for all threads to end")
        tuThreads.weld()
    except:
        Debug("[Service] Following error was caught here")
        e = sys.exc_info()
        Debug("[Service] Requesting all TU threads finish up")
        tuThreads.finishUp()
        Debug("[Service] Waiting for all threads to end")
        tuThreads.weld()
        Debug("[Service] Cleaning up db")
        trakt_cache.close()
        Debug("[Service] Dieing");
        raise e[1], None, e[2]
    Debug("[Service] Cleaning up db")
    trakt_cache.close()
    Debug("[Service] Closing");
    
if __name__ == "__main__" :
    autostart()
