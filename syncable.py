# -*- coding: utf-8 -*-
# 

from ids import RemoteId, LocalId

__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

class Syncable:
    
    def __iter__(self):
        for key in self.keys():
            yield key

    def __contains__(self, item):
        return item in self.keys()

    @classmethod
    def keys(cls):
        return cls._unsafeProperties

    @classmethod
    def setFromTrakt(cls, key, array):
        set = []
        if array is None: raise TypeError("Needed an iterable type, usually an array but got NoneType")
        for item in array:
            local = cls.fromTrakt(item)
            local[key] = True
            set.append(local)
        return set

    @classmethod
    def setFromXbmc(cls, key, array):
        set = []
        if array is None: raise TypeError("Needed an iterable type, usually an array but got NoneType")
        for item in array:
            local = cls.fromXbmc(item)
            local[key] = True
            set.append(local)
        return set

    #Merging object data
    @staticmethod
    def mergeListStatic(list):
        movie = {}
        for item in list:
            Syncable.mergeStatic(movie, item)
        return movie
    
    @staticmethod
    def mergeStatic(a, b):
        out = a
        for key in b.keys():
            if key in out:
                if key in ('rating', 'playcount', '_remoteIds', 'localIds'):
                    if key == '_rating':
                        out['rating'] = max(a['rating'], b['rating'])
                    elif key == '_playcount':
                        out['playcount'] = max(a['playcount'], b['playcount'])
                    elif key == '_remoteIds':
                        providers = b[key].keys()
                        for provider in providers:
                            if provider not in a[key] or a[key][provider] <> b[key][provider]:
                                a[key][provider] = b[key][provider]
                    elif key == '_localIds':
                        for id in b[key]:
                            if id not in a[key]:
                                a[key].append(id)

                else:
                    pass #conflict
            else:
                out[key] = b[key]
        return out
    
    #Merging objects
    def merge(self, other):
        self |= other
        return self

    def mergeList(self, others):
        for other in others:
            self |= other
        return self

    def __ior__(self, other):
        if self == other:
            return
        for key in other.keys():
            if key in self:
                if key in ('_rating', '_playcount'):
                    out[key] = max(a[key], b[key])
                elif key == '_remoteIds':
                    idsS = self[key]
                    sources = {}
                    for id in idsS:
                        sources[id.source] = id
                    idsO = other[key]
                    for id in idsO:
                        if id.source not in sources.keys() or id.remoteId <> sources[id.source].remoteId:
                            id.movie = this
                        else:
                            id.destroySelf()
                elif key == '_localIds':
                    idsS = self[key]
                    ids = []
                    for id in idsS:
                        ids.append(id.localId)
                    idsO = other[key]
                    for id in idsO:
                        if id.localId not in ids.keys():
                            id.movie = this
                        else:
                            id.destroySelf()


                else:
                    pass #conflict
            else:
                self[key] = other[key]
        other.destroySelf()

    #Enumerate diff
    def __xor__(self, others):
        left = other[0]
        right = other[1]
        return self.diff(left, right)

    def diff(self, left, right, keys=None):
        changes = []
        if keys is None:
            keys = self.keys();
        if left is None: left = {}
        if right is None: right = {}
        for key in keys:
            cacheV = self[key]
            cacheN = cacheV is None
            leftN = not key in left or left[key] is None
            rightN = not key in right or right[key] is None
            soft = key in self._lastUpdate
            leftD = leftN or left[key] <> cacheV
            rightD = rightN or right[key] <> cacheV
            sidesD = (leftN or rightN) or left[key] <> right[key]
            if cacheN: # if cache null
                if not (leftN and rightN): # if not all null
                    if leftN: # if left null
                        changes.append({'instance': self, 'dest': 'cache', 'subject': key, 'value': right[key], 'soft': True})# <~
                    elif rightN:# if right null
                        changes.append({'instance': self, 'dest': 'cache', 'subject': key, 'value': left[key], 'soft': True})# >~
                    else:
                        if sidesD:# if sides differ
                            changes.append(best({'instance': self, 'dest': 'cache', 'subject': key, 'value': left[key], 'soft': False},{'instance': self, 'dest': 'cache', 'subject': key, 'value': right[key], 'soft': False}))# ? fight
                        else:# else
                            changes.append({'instance': self, 'dest': 'cache', 'subject': key, 'value': left[key], 'soft': False})# ><
            elif not (leftN or cacheN or rightN) and (not (leftD or rightD or sidesD or soft) or ((leftD <> rightD) and soft)):# elif all not null and (all same and not soft) or (only 1 side same and soft)
                changes.append(Syncable.best({'instance': self, 'dest': 'cache', 'subject': key, 'value': left[key], 'soft': False},{'instance': self, 'dest': 'cache', 'subject': key, 'value': right[key], 'soft': False}))# ? fight
            elif leftD and not leftN:# elif left differs and isn't null
                if rightN and soft:# if right null and cache soft
                    changes.append({'instance': self, 'dest': 'cache', 'subject': key, 'value': left[key], 'soft': True})# >~
                elif rightN or rightD:# elif right null or right differs
                    changes.append({'instance': self, 'dest': 'right', 'subject': key, 'value': left[key], 'soft': False})# >
                else:# else (both sides had same change)
                    changes.append({'instance': self, 'dest': 'cache', 'subject': key, 'value': left[key], 'soft': False})# ><
            elif rightD and not rightN:# elif right differs and isn't null
                if soft:# if soft
                    changes.append({'instance': self, 'dest': 'cache', 'subject': key, 'value': right[key], 'soft': True})# <~
                else:# else
                    changes.append({'instance': self, 'dest': 'left', 'subject': key, 'value': right[key], 'soft': False})# <
            # else
                # do nothing
        return changes

    """
    Three way compare logic
    LCR /  ~  (soft = False /, True ~)
    ??? -  -  (L = left, C = cache, R = right)
    ??1 <~ -  (? input (L or R) = unknown)
    ?1? -  -  (? input C = cache empty)
    ?11 <  -  (? result = compare and decide)
    ?12 <  <~ (- = do nothing)
    1?? >~ -  (< = send R to L then C)
    1?1 >< -  (> = send L to R then C)
    1?2 ?  -  (<~ = send R to C, leave soft)
    11? >  -  (>~ = send L to C, leave soft)
    111 -  -  (>< = send L or R to C (L & R must have been the same))
    112 <  ?
    12? >  >~
    121 >< ><
    122 >  ?
    123 ?  ?
    """

    @staticmethod
    def best(change1, change2):
        if change1['subject'] <> change2['subject']:
            raise RuntimeException
        if change1['value'] >= change2['value']:
            return change1
        else:
            return change2


    # Set syncing
    @classmethod
    def diffSet(cls, key, lefts, rights):
        links = Syncable.link(lefts, rights)
        links = cls.linkCache(links)
        #import pprint
        #pprint.pprint(links)
        changes = []
        for link in links:
            changes.append(link[1].diff(link[0], link[2]))
        return changes

    @staticmethod
    def diffSetPositive(key, left, cache, right):
        changes = self.diffSet(key, left, right)
        posChanges = []
        for change in changes:
            try:
                if change['value']:
                    posChanges.append(change)
            except KeyError:
                pass
        return posChanges

    @staticmethod
    def link(lefts, rights):
        lefts = lefts or []
        rights = rights or []
        foundId = {}
        linkId = -1
        links = {}
        for left in lefts:
            linkId += 1
            links[linkId] = [left, None, None]
            try:
                for source in left['_remoteIds'].keys():
                    if not source in foundId:
                        foundId[source] = {}
                    try:
                        id = left['_remoteIds'][source]
                    except KeyError:
                        continue
                    lId = foundId[source][id]
                    cur = links[lId][0]
                    left = Syncable.mergeStatic(cur, left)
                    del links[lId]
                    foundId[source][id] = linkId
            except KeyError:
                pass
        for right in rights:
            linkId += 1
            links[linkId] = [None, None, right]
            try:
                for source in right['_remoteIds'].keys():
                    if not source in foundId:
                        foundId[source] = {}
                    try:
                        id = right['_remoteIds'][source]
                    except KeyError:
                        continue
                    lId = foundId[source][id]
                    cur = links[lId][2]
                    links[linkId][0] = links[lId][0]
                    if cur is None:
                        links[linkId][2] = right
                    else:
                        links[linkId][2] = Syncable.mergeStatic(cur, right)
                    del links[lId]
                    foundId[source][id] = linkId
                    # find others with same id and change them
                    for source in foundId.keys():
                        for id in foundId[source]:
                            if foundId[source][id] == lId:
                                foundId[source][id] = linkId
            except KeyError:
                pass

        #import pprint
        #pprint.pprint(links)
        returnLinks = []
        for linkId in links:
            returnLinks.append(links[linkId])
        return returnLinks

    @classmethod
    def linkCache(cls, links):
        outLinks = []
        for link in links:
            matched = []
            try:
                matched += cls.search(link[0])
            except TypeError, KeyError:
                pass
            try:
                matched += cls.search(link[2])
            except TypeError, KeyError:
                pass
            if len(matched) > 0:
                first = matched.pop()
                print repr(matched)
                first.mergeList(matched)
                link[1] = first     
            else:
                link[1] = cls.placeholder(link[0], link[2])
            outLinks.append(link)
        return outLinks;

    @classmethod
    def find(cls, instance):
        matched = search(instance)
        if len(matched) > 0:
            first = matched.pop()
            first.mergeList(matched)
            return first     
        else:
            return cls.placeholder(instance)

    @staticmethod
    def search(instance):
        results = []
        if '_remoteIds' in instance:
            for source in instance['_remoteIds']:
                results += RemoteId.selectBy(source=source, remoteid=instance['_remoteIds'][source])
        if '_localIds' in instance:
            for localId in instance['_localIds']:
                results += LocalId.selectBy(localid=localId)
        results = [result.get() for result in results]
        return results

    @classmethod
    def placeholder(cls, *instances):
        new = cls()
        for instance in instances:
            if instance is None: continue
            if '_remoteIds' in instance:
                for source in instance['_remoteIds']:
                    RemoteId(instance=new, source=source, remoteid=instance['_remoteIds'][source])
            if '_localIds' in instance:
                for localId in instance['_localIds']:
                    LocalId(instance=new, type=cls.__name__.lower(), localid=localId)
        return new

    @staticmethod
    def testLefts():
        return [
            {
                '_remoteIds': {'tmdb': 53223},
                '_title': "A"
            },
            {
                '_remoteIds': {'imdb': 31524, 'tmdb': 53223},
                '_title': "A"
            },
            {
                '_remoteIds': {'imdb': 679, 'tmdb': 8547},
                '_title': "C"
            },
            {
              '_remoteIds': {'tmdb': 1235},
                '_title': "D"
            },
            {
              '_remoteIds': {'tmdb': 23728},
                '_title': "E"
            }
        ]

    @staticmethod
    def testRights():
        return [
            {
                '_remoteIds': {'tmdb': 53223},
                '_title': "A"
            },
            {
                '_remoteIds': {'imdb': 31524},
                '_title': "A"
            },
            {
                '_remoteIds': {'tmdb': 8547},
                '_title': "C"
            },
            {
              '_remoteIds': {'imdb': 2473, 'tmdb': 1235},
                '_title': "D"
            },
            {
              '_remoteIds': {'imdb': 5732},
                '_title': "F"
            }
        ]

    @staticmethod
    def test():
        Syncable.link(Syncable.testLefts(), Syncable.testRights())
        TestType.create({'tmdb': 1235}, "D")
        TestType.create({'tmdb': 8547}, "C")
        TestType.create({'imdb': 5732}, "F")
        TestType.diffSet(None, Syncable.testLefts(),Syncable.testRights())

testItems = []

class TestType(Syncable):
    _unsafeProperties = ('_title',)

    @staticmethod
    def find(ids):
        raise Exception("Stupid")
        #Search the cache for the correct 
        matches = []
        for item in testItems:
            if item.matches(ids):
                matches.append(item)
        print matches
        return matches
    
    _title = ""
    _remoteIds = {}

    _bestBefore = {}
            
    def __repr__(self):
        return "<"+repr(self._title)+">"
        
    def __str__(self):
        return unicode(self._title)
    
    def __getitem__(self, index):
        if index == "_title": return self._title
    
    def __setitem__(self, index, value):
        if index == "_title": self._title = value

    def matches(self, ids):
        for source in ids:
            if source in self._remoteIds:
                if self._remoteIds[source] == ids[source]:
                    return True
        return False

    @staticmethod
    def create(remoteIds, title):
        obj = TestType()
        obj._remoteIds = remoteIds
        obj._title = title

        testItems.append(obj)
        return obj

    def destroySelf(self):
        testItems.remove(self)
