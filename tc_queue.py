from sqlobject import *
from identifiable_object import IdentifiableObject

from utilities import Debug

class TCQueue(SQLObject):
	dest = StringCol()
	instance = SingleJoin('IdentifiableObject')
	subject = StringCol()
	value = PickleCol()
	soft = BoolCol()

	@staticmethod
	def add(args):
		""" Add either a list of items or a single item
		Each item is a dictionary of 'dest', 'instance'
		, 'subject' and 'soft'"""

		try:
			for item in args:
				try:
					if not exists(*item):
						TCQueue(*item)
				except KeyError:
					continue
		except:
			raise


	def exists(dest, instance, subject, value, soft):
		if not soft and TCQueue.select(
			AND(
				TCQueue.q.dest == dest,
				AND(
					TCQueue.q.instance == instance,
					AND(
						TCQueue.q.subject == subject,
						AND(
							TCQueue.q.value == value, TCQueue.q.soft == true
							)
						)
					)
				)
			).count() == 0:
			return false
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
			return false
		return true