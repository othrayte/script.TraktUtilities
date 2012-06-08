# -*- coding: utf-8 -*-
# 

from sqlobject import *
from sqlobject.inheritance import *

__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

class IdentifiableObject(InheritableSQLObject):
    _remoteIds = MultipleJoin('RemoteId', joinColumn='instance_id')
    _localIds = MultipleJoin('LocalId', joinColumn='instance_id')