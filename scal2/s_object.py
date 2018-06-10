import os
from os.path import isfile

from scal2.json_utils import *
from scal2.core import myRaise, dataToJson

class SObjBase:
	params = ()## used in getData and setData and copyFrom
	def copyFrom(self, other):
		from copy import deepcopy
		for attr in self.params:
			try:
				value = getattr(other, attr)
			except AttributeError:
				continue
			setattr(
				self,
				attr,
				deepcopy(value),
			)
	def copy(self):
		newObj = self.__class__()
		newObj.copyFrom(self)
		return newObj
	getData = lambda self:\
		dict([(param, getattr(self, param)) for param in self.params])
	def setData(self, data):
		#if isinstance(data, dict):## FIXME
		for key, value in data.items():
			if key in self.params:
				setattr(self, key, value)
	def getIdPath(self):
		try:
			parent = self.parent
		except AttributeError:
			raise NotImplementedError('%s.getIdPath: no parent attribute'%self.__class__.__name__)
		try:
			_id = self.id
		except AttributeError:
			raise NotImplementedError('%s.getIdPath: no id attribute'%self.__class__.__name__)
		######
		path = []
		if _id is not None:
			path.append(_id)
		if parent is None:
			return path
		else:
			return parent.getIdPath() + path
	def getPath(self):
		parent = self.parent
		if parent is None:
			return []
		index = parent.index(self.id)
		return parent.getPath() + [index]


def makeOrderedData(data, params):
	if isinstance(data, dict):
		if params:
			data = data.items()
			def paramIndex(key):
				try:
					return params.index(key)
				except ValueError:
					return len(params)
			data.sort(key=lambda x: paramIndex(x[0]))
			data = OrderedDict(data)
	return data


class JsonSObjBase(SObjBase):
	file = ''
	paramsOrder = ()
	getDataOrdered = lambda self: makeOrderedData(self.getData(), self.paramsOrder)
	getJson = lambda self: dataToJson(self.getDataOrdered())
	setJson = lambda self, jsonStr: self.setData(jsonToData(jsonStr))
	def save(self):
		jstr = self.getJson()
		open(self.file, 'w').write(jstr)
	def load(self):
		if not isfile(self.file):
			raise IOError('error while loading json file %r: no such file'%self.file)
			if hasattr(self, 'modified'):
				self.setModifiedFromFile()
		else:
			'no modified param'
		jstr = open(self.file).read()
		if jstr:
			self.setJson(jstr)## FIXME
	def setModifiedFromFile(self):
		try:
			self.modified = int(os.stat(self.file).st_mtime)
		except OSError:
			pass

