# -*- coding: utf-8 -*-
# 

import os, sys
import time, socket
import threading
    
__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

class AsyncCloseRequest(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    

_Pool__pools = []
_Pool__globalPool = None

# Allows a series of functions to be called async
class Pool():

    def __init__(self, numThreads):
        _Pool__pools.append(self)
        self.slots = numThreads
        self.currentThreads = []
        self.slotCount = 0
        self.queueCount = 0
        self.event = threading.Condition()
        self.closing = False
    
    def x(self, func, *args, **kwargs):
        return AsyncCall(func, pool=self, *args, **kwargs)
    
    def map(self, func, vals):
        results = []
        for val in vals:
            results.append(self.x(func, val))
        out = []
        for result in results:
            out.append(result.need())
        return out
        
    def join(self):
        self.event.acquire()
        if self.closing:
            raise AsyncCloseRequest('')
        while self.slotCount > 0 or self.queueCount > 0:
            if self.closing:
                raise AsyncCloseRequest('')
            self.event.wait()
        self.event.release()
    
    def finishUp(self):
        self.event.acquire()
        self.closing = True
        self.event.notifyAll()
        self.event.release()
        return self

    def weld(self):
        self.event.acquire()
        while self.slotCount > 0 or self.queueCount > 0:
            self.event.notifyAll()
            self.event.wait()
        self.event.release()
        
    def safeExitPoint(self):
        self.event.acquire()
        if self.closing:
            raise AsyncCloseRequest('')
        self.event.release()

        
    def useSlot(self, thread):
        self.event.acquire()
        self.queueCount +=1
        if self.closing:
            raise AsyncCloseRequest('')
        while self.slotCount >= self.slots:
            self.event.wait()
            if self.closing:
                raise AsyncCloseRequest('')
        self.slotCount += 1
        self.queueCount -= 1
        self.currentThreads.append(thread)
        self.event.notify()
        self.event.release()
        
    def freeSlot(self, thread):
        self.event.acquire()
        self.slotCount -= 1
        self.currentThreads.remove(thread)
        self.event.notify()
        self.event.release()

    @staticmethod
    def setGlobalPool(pool):
        global _Pool__globalPool
        _Pool__globalPool = pool

    @staticmethod
    def getGlobalPool():
        global _Pool__globalPool
        if _Pool__globalPool is None:
            _Pool__globalPool = Pool(10)
        return _Pool__globalPool

def safeExitPoint():
    pool = Pool.getGlobalPool()
    pool.event.acquire()
    closing = pool.closing
    pool.event.release()
    if closing:
        raise AsyncCloseRequest('')

class AsyncCall():
    
    def __init__(self, func, pool='default', *args, **kwargs):
        self.func = func
        if pool is not None and pool == 'default':
            self.pool = Pool.getGlobalPool()
        else:
            self.pool = pool
        self.args = args
        self.kwargs = kwargs
        self.result = None
        self.e = None
        self._ignore = False
        self.returned = False
        self.closing = False
        self.event = threading.Condition()
        self.thread = threading.Thread(target=self.__runner)
        if self.pool is not None: self.pool.useSlot(self.thread)
        self.thread.start()
    def __invert__(self):
        return self.need()
        
    def __runner(self):
        try:
            r = self.func(*self.args, **self.kwargs)
        except AsyncCloseRequest, acr:
            import sys
            self.event.acquire()
            self.returned = True
            self.e = sys.exc_info()
            self.event.notify()
            self.event.release()
            if self.pool is not None: self.pool.finishUp()

        except Exception, e:
            import sys
            self.event.acquire()
            self.returned = True
            self.e = sys.exc_info()
            self.event.notify()
            self.event.release()
            if self._ignore:
                print self.e
                raise
        else:
            self.event.acquire()
            self.returned = True
            self.result = r
            self.event.notify()
            self.event.release()
        finally:    
            if self.pool is not None: self.pool.freeSlot(self.thread)
        
    def need(self):
        self.event.acquire()
        while not self.returned:
            if self.closing:
                raise AsyncCloseRequest('')
            self.event.wait()
        self.event.release()
        if self.e is not None:
            raise self.e[1], None, self.e[2]
        return self.result
    
    def ignore(self):
        self.event.acquire()
        self._ignore = True
        self.event.release()
        if self.e is not None:
            raise self.e[1], None, self.e[2]

def async(func):
    def wrapper(*args, **kwargs):
        if 'pool' in kwargs:
            pool = kwargs['pool']
        else:
            pool = 'default'
        #print globals()
        #globals()[func.__module__].__dict__[func.__name__] = func
        return AsyncCall(func, pool, *args, **kwargs)
    return wrapper