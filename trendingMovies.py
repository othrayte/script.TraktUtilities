# -*- coding: utf-8 -*-
# @author Ralph-Gordon Paul, Adrian Cowan (othrayte)
# 

import os
import xbmc,xbmcaddon,xbmcgui
from utilities import *

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
        pass
 
    def onInit(self):
        # Put your List Populating code/ and GUI startup stuff here
        self.getControl(180).setLabel("Trakt - "+__language__(1250).encode( "utf-8", "ignore" ))
        mylist = self.getControl(181)
        items = []
        for movie in self.movies:
            item = xbmcgui.ListItem(movie['title'].encode( "utf-8", "ignore" ), str(movie['year']), movie['images']['poster'].encode( "utf-8", "ignore" ))
            items.append(item)
            print movie['title'].encode( "utf-8", "ignore" )    
        mylist.addItems(items)
        self.onChange()
        pass 
    
    def setData(self, data):
        self.movies = data    
    
    def onChange(self):
        mylist = self.getControl(181)
        self.current = mylist.getSelectedPosition()
        self.getControl(182).setImage(str(self.movies[self.current]['images']['fanart'].encode( "utf-8", "ignore" )))
        self.getControl(183).setLabel(self.movies[self.current]['title'].encode( "utf-8", "ignore" )+" ["+str(self.movies[self.current]['year'])+"]\n")
        info =  "Watchers: "+str(self.movies[self.current]['watchers']).encode( "utf-8", "ignore" )+"\n"
        info += "Runtime: "+str(self.movies[self.current]['runtime']).encode( "utf-8", "ignore" )+"mins\n"
        info += "Rating: "+self.movies[self.current]['certification'].encode( "utf-8", "ignore" )
        self.getControl(184).setLabel(info)
        self.getControl(185).setEnabled(self.movies[self.current]['idMovie'] != -1) # Disable the play button if movie not found in collection
    
    def onAction(self, action):
        # Same as normal python Windows.
        print action.getId()
        if action.getId() in (9,10):
            self.close()
        elif action.getId() in (1,2,107):
            self.onChange()
        pass
    
    def onClick(self, controlID):
        """
            Notice: onClick not onControl
            Notice: it gives the ID of the control not the control object
        """
        if controlID in (181,185):
            if (self.movies[self.current]['idMovie'] != -1):
                playMovieById(self.movies[self.current]['idMovie'])
        elif controlID == 186:
            xbmcgui.Dialog().ok("Trakt Utilities", "comming soon")
        else:
            print "Other control clicked: "+str(controlID)
        pass
 
    def onFocus(self, controlID):
        pass
