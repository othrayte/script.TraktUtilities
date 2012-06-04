

class Syncable:
    
    def __iter__(self):
        for key in __unsafeProperties:
            yield key

    def __contains__(self, item):
        return item in __unsafeProperties
    
    def keys():
        return __unsafeProperties

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

    def __ior__(self, other):
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
        for key in keys:
            cacheV = self[key]
            cacheN = cacheV is Null
            leftN = left[key] is Null
            rightN = right[key] is Null
            soft = key in _bestBefore
            leftD = left[key] <> cacheV
            rightD = right[key] <> cacheV
            sidesD = left[key] <> right[key]
            if cacheN: # if cache null
                if not leftN and not rightN: # if not all null
                    if leftN: # if left null
                        changes.append({'dest': 'cache', 'instance': self, 'subject': key, 'value': right[key], 'soft': true})# <~
                    elif rightN:# if right null
                        changes.append({'dest': 'cache', 'instance': self, 'subject': key, 'value': left[key], 'soft': true})# >~
                    else:
                        if sidesD:# if sides differ
                            changes.append(best({'dest': 'cache', 'instance': self, 'subject': key, 'value': left[key], 'soft': false},{'dest': 'cache', 'instance': self, 'subject': key, 'value': right[key], 'soft': false}))# ? fight
                        else:# else
                            changes.append({'dest': 'cache', 'instance': self, 'subject': key, 'value': left[key], 'soft': false})# ><
            elif not (leftN or cacheN or rightN) and (not (leftD or rightD or sidesD or soft) or ((leftD <> rightD) and soft)):# elif all not null and (all same and not soft) or (only 1 side same and soft)
                changes.append(best({'dest': 'cache', 'instance': self, 'subject': key, 'value': left[key], 'soft': false},{'dest': 'cache', 'instance': self, 'subject': key, 'value': right[key], 'soft': false}))# ? fight
            elif leftD and not leftN:# elif left differs and isn't null
                if rightN and soft:# if right null and cache soft
                    changes.append({'dest': 'cache', 'instance': self, 'subject': key, 'value': left[key], 'soft': true})# >~
                elif rightN or rightD:# elif right null or right differs
                    changes.append({'dest': 'right', 'instance': self, 'subject': key, 'value': left[key], 'soft': false})# >
                else:# else (both sides had same change)
                    changes.append({'dest': 'cache', 'instance': self, 'subject': key, 'value': left[key], 'soft': false})# ><
            elif rightD and not rightN:# elif right differs and isn't null
                if soft:# if soft
                    changes.append({'dest': 'cache', 'instance': self, 'subject': key, 'value': right[key], 'soft': true})# <~
                else:# else
                    changes.append({'dest': 'left', 'instance': self, 'subject': key, 'value': right[key], 'soft': false})# <
            # else
                # do nothing

    """
    Three way compare logic
    LCR /  ~  (soft = false /, true ~)
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

    # Set syncing
    @staticmethod
    def diffSet(key, lefts, type, rights):
        return []
    """    cur = {}
        leftNew = []
        rightNew = []
        for left in lefts:
            id = type.find(left)
            if id is None:
                leftNew.append(left)
            else:
                cur[id] = (left, None)
        for right in rights:
            id = type.find(right)
            if id is None:
                rightNew.append(right)
            else:
                if id in cur:
                    cur[id] = (cur[id][0], right)
                else:
                    cur[id] = (None, right)
        type.get
        for left in leftNew:
            if 
        diff()
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
        return posChanges"""

    @staticmethod
    def link(lefts, rights):
        foundId = {}
        linkId = -1
        links = {}
        for left in lefts:
            linkId += 1
            links[linkId] = [left, None]
            try:
                for source in left['remoteIds'].keys():
                    if not source in foundId:
                        foundId[source] = {}
                    try:
                        id = left['remoteIds'][source]
                        print id
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
            links[linkId] = [None, right]
            try:
                for source in right['remoteIds'].keys():
                    if not source in foundId:
                        foundId[source] = {}
                    try:
                        id = right['remoteIds'][source]
                        print id
                        lId = foundId[source][id]
                        cur = links[lId][1]
                        links[linkId][0] = links[lId][0]
                        if cur is None:
                            links[linkId][1] = right
                        else:
                            links[linkId][1] = Syncable.mergeStatic(cur, right)
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
                'title': "A"
            },
            {
                'remoteIds': {'imdb': 31524, 'tmdb': 53223},
                'title': "A"
            },
            {
                'remoteIds': {'imdb': 679, 'tmdb': 8547},
                'title': "C"
            },
            {
              'remoteIds': {'tmdb': 1235},
                'title': "D"
            },
            {
              'remoteIds': {'tmdb': 23728},
                'title': "E"
            }
        ]

    @staticmethod
    def testRights():
        return [
            {
                'remoteIds': {'tmdb': 53223},
                'title': "A"
            },
            {
                'remoteIds': {'imdb': 31524},
                'title': "A"
            },
            {
                'remoteIds': {'tmdb': 8547},
                'title': "C"
            },
            {
              'remoteIds': {'imdb': 2473, 'tmdb': 1235},
                'title': "D"
            },
            {
              'remoteIds': {'imdb': 5732},
                'title': "F"
            }
        ]

    @staticmethod
    def test():
        return Syncable.link(Syncable.testLefts(), Syncable.testRights())