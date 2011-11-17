# -*- coding: utf-8 -*-
# 

import xbmc,xbmcaddon,xbmcgui
import telnetlib, time

try: import simplejson as json
except ImportError: import json

import threading
from utilities import *
from rating import *
from sync_update import *
from instant_sync import *
from scrobbler import Scrobbler

__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

__settings__ = xbmcaddon.Addon( "script.TraktUtilities" )
__language__ = __settings__.getLocalizedString

# Receives XBMC notifications and passes them off to the rating functions
class NotificationService(threading.Thread):
    abortRequested = False
    def run(self):        
        #while xbmc is running
        scrobbler = Scrobbler()
        scrobbler.start()
        
        while (not (self.abortRequested or xbmc.abortRequested)):
            try:
                tn = telnetlib.Telnet('localhost', 9090, 10)
            except IOError as (errno, strerror):
                #connection failed, try again soon
                Debug("[Notification Service] Telnet too soon? ("+str(errno)+") "+strerror)
                time.sleep(1)
                continue
            
            Debug("[Notification Service] Waiting~");
            bCount = 0
            
            while (not (self.abortRequested or xbmc.abortRequested)):
                if bCount == 0:
                    notification = ""
                    inString = False
                    
                try:
                    [index, match, raw] = tn.expect(["(\\\\)|(\\\")|[{\"}]"], 0.5) #note, pre-compiled regex might be faster here
                    notification += raw
                    Debug("[~] raw, "+repr(index)+", "+repr(match)+", "+repr(raw))
                except EOFError:
                    break #go out to the other loop to restart the connection
                    
                if index == -1: # Timeout
                    continue
                if index == 0: # Found escaped quote
                    match = match.group(0)
                    if match == "\"":
                        inString = not inString
                        continue
                    if match == "{":
                        bCount += 1
                    if match == "}":
                        bCount -= 1
                if bCount > 0:
                    continue
                if bCount < 0:
                    bCount = 0
                
                Debug("[Notification Service] message: " + str(notification))
                
                # Parse recieved notification
                data = json.loads(notification)
                
                # Forward notification to functions
                if 'method' in data and 'params' in data and 'sender' in data['params'] and data['params']['sender'] == 'xbmc':
                    if data['method'] == 'Player.OnStop':
                        scrobbler.playbackEnded()
                    elif data['method'] == 'Player.OnPlay':
                        if 'data' in data['params'] and 'item' in data['params']['data'] and 'id' in data['params']['data']['item'] and 'type' in data['params']['data']['item']:
                            scrobbler.playbackStarted(data['params']['data'])
                    elif data['method'] == 'Player.OnPause':
                        scrobbler.playbackPaused()
                    elif data['method'] == 'VideoLibrary.OnUpdate':
                        if 'data' in data['params'] and 'playcount' in data['params']['data']:
                            instantSyncPlayCount(data)
                    elif data['method'] == 'System.OnQuit':
                        self.abortRequested = True
                
            time.sleep(1)
        tn.close()
        scrobbler.abortRequested = True