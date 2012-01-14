# -*- coding: utf-8 -*-
# 

import xbmc,xbmcaddon,xbmcgui

from utilities import *
import notification_service
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
    # Initialise the cache
    trakt_cache.init(os.path.join(cacheDirectory,"trakt_cache"))
    
    # Initialise the notification handler
    notificationThread = notification_service.NotificationService()
    notificationThread.start()
    
    # Trigger update checks for the cache
    trakt_cache.trigger()
    
    # Wait for the notification handler to quit
    notificationThread.join()
    try:
        tuThreads.join()
    except AsyncCloseRequest:
        pass
    Debug("[Service] Closing");
    
if __name__ == "__main__" :
    autostart()
