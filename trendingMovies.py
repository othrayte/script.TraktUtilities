# -*- coding: utf-8 -*-
# @author Ralph-Gordon Paul, Adrian Cowan (othrayte)
# 

import os
import xbmc,xbmcaddon,xbmcgui

try:
    # Python 3.0 +
    import http.client as httplib
except ImportError:
    # Python 2.7 and earlier
    import httplib

try:
  # Python 2.6 +
  from hashlib import sha as sha
except ImportError:
  # Python 2.5 and earlier
  import sha
  
try:
    # Python 2.4
    import pysqlite2.dbapi2 as sqlite3
except:
    # Python 2.6 +
    import sqlite3 

# read settings
__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

apikey = '0a698a20b222d0b8637298f6920bf03a'
username = __settings__.getSetting("username")
pwd = sha.new(__settings__.getSetting("password")).hexdigest()
debug = __settings__.getSetting( "debug" )

class GUI(xbmcgui.WindowXML):
    def __init__(self,strXMLname, strFallbackPath, strDefaultName, forceFallback):
        # Changing the three varibles passed won't change, anything
        # Doing strXMLname = "bah.xml" will not change anything.
        # don't put GUI sensitive stuff here (as the xml hasn't been read yet
        # Idea to initialize your variables here
        self.doModal()
        pass
 
    def onInit(self):
        # Put your List Populating code/ and GUI startup stuff here
        self.getControl(180).setLabel("Trakt - Trending Movies")
        mylist = self.getControl(181)
        for movie in data:
            mylist.addControl(xbmcgui.ControlImage(10, 10, 100, 100, movie['images']['poster']))
        pass 
 
    def onAction(self, action):
        # Same as normal python Windows.
        print action.getId()
        if action.getId() in (9,10):
            self.close()
        pass
 
    def onClick(self, controlID):
        """
            Notice: onClick not onControl
            Notice: it gives the ID of the control not the control object
        """
        
        pass
 
    def onFocus(self, controlID):
        pass
