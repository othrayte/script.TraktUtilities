# -*- coding: utf-8 -*-
# 

from sqlobject import *
from identifiable_object import IdentifiableObject

from utilities import Debug
from datetime import datetime

__author__ = "Ralph-Gordon Paul, Adrian Cowan"
__credits__ = ["Ralph-Gordon Paul", "Adrian Cowan", "Justin Nemeth",  "Sean Rudford"]
__license__ = "GPL"
__maintainer__ = "Ralph-Gordon Paul"
__email__ = "ralph-gordon.paul@uni-duesseldorf.de"
__status__ = "Production"

class TCQueue(SQLObject):
	dest = StringCol()
	type = StringCol()
	instance = ForeignKey('IdentifiableObject', notNull=True)
	subject = StringCol()
	value = PickleCol()
	time = DateTimeCol()
	soft = BoolCol()

	@staticmethod
	def add(args):
		""" Add either a list of items or a single item
		Each item is a dictionary of 'dest', 'instance'
		, 'subject' and 'soft'"""

		try:
			for item in args:
				for change in item:
					try:
						if not TCQueue.exists(**change):
							change['type'] = change['instance'].__class__.__name__.lower()
							change['time'] = datetime.now()
							TCQueue(**change)
					except KeyError:
						continue
		except:
			raise

	@staticmethod
	def exists(dest, instance, subject, value, soft):
		if not soft and TCQueue.select(
			AND(
				TCQueue.q.dest == dest,
				AND(
					TCQueue.q.instance == instance,
					AND(
						TCQueue.q.subject == subject,
						AND(
							TCQueue.q.value == value, TCQueue.q.soft == True
							)
						)
					)
				)
			).count() == 0:
			return False
		elif soft and TCQueue.select(
			AND(
				TCQueue.q.dest == dest,
				AND(
					TCQueue.q.instance == instance,
					AND(
						TCQueue.q.subject == subject,
						TCQueue.q.value == value
						)
					)
				)
			).count() == 0:
			return False
		return True