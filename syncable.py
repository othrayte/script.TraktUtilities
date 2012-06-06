

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

    #Merging object data
    @staticmethod
    def mergeListStatic(list):
        movie = {}
        for item in list:
            mergeStatic(movie, item)
        return movie
    
    @staticmethod
    def mergeStatic(a, b):
        out = a
        for key in b.keys():
            if key in out:
                if key in ('rating', 'playcount', 'remoteIds', 'localIds'):
                    if key == 'rating':
                        out['rating'] = max(a['rating'], b['rating'])
                    elif key == 'playcount':
                        out['playcount'] = max(a['playcount'], b['playcount'])
                    elif key == 'remoteIds':
                        providers = b[key].keys()
                        for provider in providers:
                            if provider not in a[key] or a[key][provider] <> b[key][provider]:
                                a[key][provider] = b[key][provider]
                    elif key == 'localIds':
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
            print key in left
            leftN = not key in left or left[key] is None
            rightN = not key in right or right[key] is None
            soft = key in self._bestBefore
            leftD = leftN or left[key] <> cacheV
            rightD = rightN or right[key] <> cacheV
            sidesD = (leftN or rightN) or left[key] <> right[key]
            if cacheN: # if cache null
                if not (leftN and rightN): # if not all null
                    if leftN: # if left null
                        changes.append({'dest': 'cache', 'attr': key, 'value': right[key], 'soft': True})# <~
                    elif rightN:# if right null
                        changes.append({'dest': 'cache', 'attr': key, 'value': left[key], 'soft': True})# >~
                    else:
                        if sidesD:# if sides differ
                            changes.append(best({'dest': 'cache', 'attr': key, 'value': left[key], 'soft': False},{'dest': 'cache', 'attr': key, 'value': right[key], 'soft': False}))# ? fight
                        else:# else
                            changes.append({'dest': 'cache', 'attr': key, 'value': left[key], 'soft': False})# ><
            elif not (leftN or cacheN or rightN) and (not (leftD or rightD or sidesD or soft) or ((leftD <> rightD) and soft)):# elif all not null and (all same and not soft) or (only 1 side same and soft)
                changes.append(Syncable.best({'dest': 'cache', 'attr': key, 'value': left[key], 'soft': False},{'dest': 'cache', 'attr': key, 'value': right[key], 'soft': False}))# ? fight
            elif leftD and not leftN:# elif left differs and isn't null
                if rightN and soft:# if right null and cache soft
                    changes.append({'dest': 'cache', 'attr': key, 'value': left[key], 'soft': True})# >~
                elif rightN or rightD:# elif right null or right differs
                    changes.append({'dest': 'right', 'attr': key, 'value': left[key], 'soft': False})# >
                else:# else (both sides had same change)
                    changes.append({'dest': 'cache', 'attr': key, 'value': left[key], 'soft': False})# ><
            elif rightD and not rightN:# elif right differs and isn't null
                if soft:# if soft
                    changes.append({'dest': 'cache', 'attr': key, 'value': right[key], 'soft': True})# <~
                else:# else
                    changes.append({'dest': 'left', 'attr': key, 'value': right[key], 'soft': False})# <
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
        if change1['attr'] <> change2['attr']:
            raise RuntimeException
        if change1['value'] >= change2['value']:
            return change1
        else:
            return change2


    # Set syncing
    @staticmethod
    def diffSet(keys, lefts, type, rights):
        links = Syncable.link(lefts, rights)
        links = Syncable.linkCache(links, type)
        import pprint
        pprint.pprint(links)
        changes = []
        for link in links:
            print link
            changes.append(link[1].diff(link[0], link[2], keys))
        print changes
        return changes

    @staticmethod
    def diffSetPositive(keys, left, cache, right):
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
        foundId = {}
        linkId = -1
        links = {}
        for left in lefts:
            linkId += 1
            links[linkId] = [left, None, None]
            try:
                for source in left['remoteIds'].keys():
                    if not source in foundId:
                        foundId[source] = {}
                    try:
                        id = left['remoteIds'][source]
                        lId = foundId[source][id]
                        cur = links[lId][0]
                        left = Syncable.mergeStatic(cur, left)
                        del links[lId]
                    except KeyError:
                        pass
                    foundId[source][id] = linkId
            except KeyError:
                pass
        for right in rights:
            linkId += 1
            links[linkId] = [None, None, right]
            try:
                for source in right['remoteIds'].keys():
                    if not source in foundId:
                        foundId[source] = {}
                    try:
                        id = right['remoteIds'][source]
                        lId = foundId[source][id]
                        cur = links[lId][2]
                        links[linkId][0] = links[lId][0]
                        if cur is None:
                            links[linkId][2] = right
                        else:
                            links[linkId][2] = Syncable.mergeStatic(cur, right)
                        del links[lId]
                    except KeyError:
                        pass
                    foundId[source][id] = linkId
                    # find others with same id and change them
                    for source in foundId.keys():
                        for id in foundId[source]:
                            if foundId[source][id] == lId:
                                foundId[source][id] = linkId
            except KeyError:
                pass

        import pprint
        pprint.pprint(links)
        returnLinks = []
        for linkId in links:
            returnLinks.append(links[linkId])
        return returnLinks

    @staticmethod
    def linkCache(links, type):
        outLinks = []
        for link in links:
            matched = []
            try:
                matched += type.find(link[0]['remoteIds'])
            except TypeError, KeyError:
                pass
            try:
                matched += type.find(link[2]['remoteIds'])
            except TypeError, KeyError:
                pass
            if len(matched) > 0:
                first = matched.pop()
                first.mergeList(matched)
                link[1] = first     
            else:
                link[1] = TestType.create({}, None)
            outLinks.append(link)
        return outLinks;

    @staticmethod
    def find(remoteId=None, localId=None):
        if remoteId is None and localId is None:
            raise ValueError("Must provide at least one form of id")
        if remoteId is not None and 'source' in remoteId and 'remoteid' in remoteId:
            try:
                item = RemoteId.selectBy(*remoteId).getOne()
                return item.get()
            except SQLObjectNotFound:
                pass
            except SQLObjectIntegrityError:
                Debug("[Syncable] Warning integrity error, multiple results for one set")
                return None
        if localId is not None:
            try:
                item = LocalId.byLocalid(localId).getOne()
                return item.get()
            except SQLObjectNotFound:
                pass
            except SQLObjectIntegrityError:
                Debug("[Syncable] Warning integrity error, multiple results for one set")
                return None
        #Not found
        return None

    @staticmethod
    def testLefts():
        return [
            {
                'remoteIds': {'tmdb': 53223},
                '_title': "A"
            },
            {
                'remoteIds': {'imdb': 31524, 'tmdb': 53223},
                '_title': "A"
            },
            {
                'remoteIds': {'imdb': 679, 'tmdb': 8547},
                '_title': "C"
            },
            {
              'remoteIds': {'tmdb': 1235},
                '_title': "D"
            },
            {
              'remoteIds': {'tmdb': 23728},
                '_title': "E"
            }
        ]

    @staticmethod
    def testRights():
        return [
            {
                'remoteIds': {'tmdb': 53223},
                '_title': "A"
            },
            {
                'remoteIds': {'imdb': 31524},
                '_title': "A"
            },
            {
                'remoteIds': {'tmdb': 8547},
                '_title': "C"
            },
            {
              'remoteIds': {'imdb': 2473, 'tmdb': 1235},
                '_title': "D"
            },
            {
              'remoteIds': {'imdb': 5732},
                '_title': "F"
            }
        ]

    @staticmethod
    def test():
        Syncable.link(Syncable.testLefts(), Syncable.testRights())
        TestType.create({'tmdb': 1235}, "D")
        TestType.create({'tmdb': 8547}, "C")
        TestType.create({'imdb': 5732}, "F")
        Syncable.diffSet(None, Syncable.testLefts(), TestType,Syncable.testRights())

testItems = []

class TestType(Syncable):
    _unsafeProperties = ('_title',)

    @staticmethod
    def find(ids):
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
