

class Syncable:
    
    def __iter__(self):
        for key in __unsafeProperties:
            yield key

    def __contains__(self, item):
        return item in __unsafeProperties
    
    def keys():
        return __unsafeProperties

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
    def diff(self, left, right):
        return self ^ (left, right)

    def __xor__(self, others):
        left = other[0]
        right = other[1]
        changes = []
        for key in self.keys():
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
                        changes.append({'dest': 'cache', 'attr': key, 'value': right[key], 'soft': true})# <~
                    elif rightN:# if right null
                        changes.append({'dest': 'cache', 'attr': key, 'value': left[key], 'soft': true})# >~
                    else:
                        if sidesD:# if sides differ
                            changes.append(best({'dest': 'cache', 'attr': key, 'value': left[key], 'soft': false},{'dest': 'cache', 'attr': key, 'value': right[key], 'soft': false}))# ? fight
                        else:# else
                            changes.append({'dest': 'cache', 'attr': key, 'value': left[key], 'soft': false})# ><
            elif not (leftN or cacheN or rightN) and (not (leftD or rightD or sidesD or soft) or ((leftD <> rightD) and soft)):# elif all not null and (all same and not soft) or (only 1 side same and soft)
                changes.append(best({'dest': 'cache', 'attr': key, 'value': left[key], 'soft': false},{'dest': 'cache', 'attr': key, 'value': right[key], 'soft': false}))# ? fight
            elif leftD and not leftN:# elif left differs and isn't null
                if rightN and soft:# if right null and cache soft
                    changes.append({'dest': 'cache', 'attr': key, 'value': left[key], 'soft': true})# >~
                elif rightN or rightD:# elif right null or right differs
                    changes.append({'dest': 'right', 'attr': key, 'value': left[key], 'soft': false})# >
                else:# else (both sides had same change)
                    changes.append({'dest': 'cache', 'attr': key, 'value': left[key], 'soft': false})# ><
            elif rightD and not rightN:# elif right differs and isn't null
                if soft:# if soft
                    changes.append({'dest': 'cache', 'attr': key, 'value': right[key], 'soft': true})# <~
                else:# else
                    changes.append({'dest': 'left', 'attr': key, 'value': right[key], 'soft': false})# <
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
    def setDiff(self, key, left, right):
    	changes = self.setDiffPositive(key, left, right)
    	changes += self.setDiffNegative(key, left, right)
    	return changes

    def setDiffPositive(self, key, left, right):
    	

    def setDiffNegative(self, key, left, right):
