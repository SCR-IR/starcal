#!/usr/bin/env python3
import sys
import os
from os.path import isfile, join
from time import time as now
from collections import OrderedDict

from hashlib import sha1

from scal3.path import objectDir, rootDir

sys.path.insert(0, join(rootDir, "libs", "bson"))
import bson

from scal3.os_utils import makeDir
from scal3.json_utils import *
from scal3.utils import myRaise

dataToJson = dataToPrettyJson
#from scal3.core import dataToJson## FIXME


class SObj:
	@classmethod
	def getSubclass(cls, _type):
		return cls

	params = ()  # used in getData, setData and copyFrom
	canSetDataMultipleTimes = True

	def __nonzero__(self):
		return self.__bool__()

	def __bool__(self):
		raise NotImplementedError

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

	def getData(self):
		return {
			param: getattr(self, param)
			for param in self.params
		}

	def setData(self, data, force=False):
		if not force and not self.__class__.canSetDataMultipleTimes:
			if getattr(self, "dataIsSet", False):
				raise RuntimeError(
					"can not run setData multiple times for %s instance" %
					self.__class__.__name__
				)
			self.dataIsSet = True
		###########
		#if isinstance(data, dict):## FIXME
		for key, value in data.items():
			if key in self.params:
				setattr(self, key, value)

	def getIdPath(self):
		try:
			parent = self.parent
		except AttributeError:
			raise NotImplementedError(
				"%s.getIdPath: no parent attribute" % self.__class__.__name__
			)
		try:
			_id = self.id
		except AttributeError:
			raise NotImplementedError(
				"%s.getIdPath: no id attribute" % self.__class__.__name__
			)
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
			data = list(data.items())

			def paramIndex(key):
				try:
					return params.index(key)
				except ValueError:
					return len(params)

			data.sort(key=lambda x: paramIndex(x[0]))
			data = OrderedDict(data)

	return data


def getSortedDict(data):
	return OrderedDict(sorted(data.items()))


class JsonSObj(SObj):
	canSetDataMultipleTimes = False
	skipLoadExceptions = False
	skipLoadNoFile = False
	file = ""
	paramsOrder = ()

	@classmethod
	def getFile(cls, _id=None):
		return cls.file

	@classmethod
	def load(cls, *args):
		_file = cls.getFile(*args)
		data = {}
		if isfile(_file):
			try:
				jsonStr = open(_file).read()
				data = jsonToData(jsonStr)
			except Exception as e:
				if not cls.skipLoadExceptions:
					raise e
		else:
			if not cls.skipLoadNoFile:
				raise FileNotFoundError("%s : file not found" % _file)

		# data is the result of json.loads, so probably can be just dict or list (or str)
		_type = data.get("type") if isinstance(data, dict) else None
		if _type is None:
			subCls = cls
		else:
			subCls = cls.getSubclass(_type)
		obj = subCls(*args)
		obj.setData(data)
		return obj
	#####

	def getDataOrdered(self):
		return makeOrderedData(self.getData(), self.paramsOrder)

	def getJson(self):
		return dataToJson(self.getDataOrdered())

	def setJson(self, jsonStr):
		return self.setData(jsonToData(jsonStr))

	def save(self):
		if self.file:
			jstr = self.getJson()
			open(self.file, "w").write(jstr)
		else:
			print(
				"save method called for object %r" % self +
				" while file is not set"
			)

	def setData(self, data):
		SObj.setData(self, data)
		self.setModifiedFromFile()

	def setModifiedFromFile(self):
		if hasattr(self, "modified"):
			try:
				self.modified = int(os.stat(self.file).st_mtime)
			except OSError:
				pass
		#else:
		#	print("no modified param for object %r"%self)


def saveBsonObject(data):
	data = getSortedDict(data)
	bsonBytes = bytes(bson.dumps(data))
	_hash = sha1(bsonBytes).hexdigest()
	dpath = join(objectDir, _hash[:2])
	fpath = join(dpath, _hash[2:])
	if not isfile(fpath):
		makeDir(dpath)
		open(fpath, "wb").write(bsonBytes)
	return _hash


def loadBsonObject(_hash):
	fpath = join(objectDir, _hash[:2], _hash[2:])
	bsonBytes = open(fpath, "rb").read()
	if _hash != sha1(bsonBytes).hexdigest():
		raise IOError(
			"sha1 diggest does not match for object file \"%s\"" % fpath
		)
	return bson.loads(bsonBytes)


def updateBasicDataFromBson(data, filePath, fileType):
	"""
		fileType: "event" | "group" | "account"...,
			display only, does not matter much
		return lastHistRecord = (lastEpoch, lastHash)
	"""
	try:
		lastHistRecord = data["history"][0]
		lastEpoch = lastHistRecord[0]
		lastHash = lastHistRecord[1]
	except (KeyError, IndexError):
		raise ValueError(
			"invalid %s file \"%s\", no \"history\"" % (fileType, filePath)
		)
	data.update(loadBsonObject(lastHash))
	data["modified"] = lastEpoch ## FIXME
	return (lastEpoch, lastHash)


class BsonHistObj(SObj):
	canSetDataMultipleTimes = False
	skipLoadExceptions = False
	skipLoadNoFile = False
	file = ""
	lastHash = None
	## basicParams or noHistParams ? FIXME
	basicParams = (
	)

	@classmethod
	def getFile(cls, _id=None):
		return cls.file

	@classmethod
	def load(cls, *args):
		_file = cls.getFile(*args)
		data = {}
		lastEpoch, lastHash = None, None
		try:
			jsonStr = open(_file).read()
			data = jsonToData(jsonStr)
		except FileNotFoundError:
			if not cls.skipLoadNoFile:
				raise FileNotFoundError("%s : file not found" % _file)
		except Exception as e:
			if not cls.skipLoadExceptions:
				print("error while opening json file \"%s\"" % _file)
				raise e
		else:
			lastEpoch, lastHash = updateBasicDataFromBson(data, _file, cls.name)

		# data is the result of json.loads, so probably can be just dict or list (or str)
		_type = data.get("type") if isinstance(data, dict) else None
		if _type is None:
			subCls = cls
		else:
			subCls = cls.getSubclass(_type)
		obj = subCls(*args)
		obj.setData(data)
		obj.lastHash = lastHash
		obj.modified = lastEpoch
		return obj
	#######

	def getDataOrdered(self):
		return makeOrderedData(self.getData(), self.paramsOrder)

	def loadBasicData(self):
		if not isfile(self.file):
			return {}
		return jsonToData(open(self.file).read())

	def loadHistory(self):
		lastBasicData = self.loadBasicData()
		history = lastBasicData.get("history")
		if history is None:
			if lastBasicData:
				print("no \"history\" in json file \"%s\"" % self.file)
			history = []
		return history

	def saveBasicData(self, basicData):
		jsonStr = dataToJson(basicData)
		open(self.file, "w").write(jsonStr)

	def save(self, *histArgs):
		"""
			returns last history record: (lastEpoch, lastHash, **args)
		"""
		if not self.file:
			raise RuntimeError(
				"save method called for object %r" % self +
				" while file is not set"
			)
		data = self.getData()
		basicData = {}
		for param in self.basicParams:
			if param not in data:
				continue
			basicData[param] = data.pop(param)
		if "modified" in data:
			del data["modified"]
		_hash = saveBsonObject(data)
		###
		history = self.loadHistory()
		###
		try:
			lastHash = history[0][1]
		except IndexError:
			lastHash = None
		if _hash != lastHash:## or lastHistArgs != histArgs:## FIXME
			tm = now()
			history.insert(0, [tm, _hash] + list(histArgs))
			self.modified = tm
		basicData["history"] = history
		self.saveBasicData(basicData)
		return history[0]

	def getRevision(self, revHash, *args):
		cls = self.__class__
		data = self.loadBasicData()
		data.update(loadBsonObject(revHash))
		try:
			_type = data["type"]
		except (KeyError, TypeError):
			subCls = cls
		else:
			subCls = cls.getSubclass(_type)
		obj = subCls(*args)
		obj.setData(data)
		return obj
