#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) Saeed Rasooli <saeed.gnu@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
# Also avalable in /usr/share/common-licenses/GPL on Debian systems
# or /usr/share/licenses/common/GPL3/license.txt on ArchLinux

from time import time as now

import sys
import os
from os import listdir
import os.path
from os.path import dirname, join, isfile, splitext, isabs

from typing import Any, Optional, Tuple, List, Sequence, Dict, Callable

from scal3.utils import cleanCacheDict, myRaise, myRaiseTback
from scal3.utils import toBytes
from scal3.json_utils import *
from scal3.path import *
from scal3.types_starcal import CellType, CompiledTimeFormat

from scal3.cal_types import calTypes, jd_to

from scal3 import locale_man
from scal3.locale_man import tr as _
from scal3.locale_man import numDecode


from scal3 import core

from scal3 import event_lib
from scal3.event_diff import EventDiff

uiName = ""


#######################################################

sysConfPath = join(sysConfDir, "ui.json")  # also includes LIVE config

confPath = join(confDir, "ui.json")

confPathCustomize = join(confDir, "ui-customize.json")

confPathLive = join(confDir, "ui-live.json")

confParams = (
	"showMain",
	"showDesktopWidget",
	"winTaskbar",
	"useAppIndicator",
	"showDigClockTr",
	"fontCustomEnable",
	"fontCustom",
	"bgUseDesk",
	"bgColor",
	"borderColor",
	"cursorOutColor",
	"cursorBgColor",
	"todayCellColor",
	"textColor",
	"holidayColor",
	"inactiveColor",
	"borderTextColor",
	"cursorDiaFactor",
	"cursorRoundingFactor",
	"statusIconImage",
	"statusIconImageHoli",
	"statusIconFontFamilyEnable",
	"statusIconFontFamily",
	"statusIconFixedSizeEnable",
	"statusIconFixedSizeWH",
	"maxDayCacheSize",
	"pluginsTextStatusIcon",
	# "localTzHist",  # FIXME
	"showYmArrows",
)

confParamsLive = (
	"winX",
	"winY",
	"winWidth",
	"winKeepAbove",
	"winSticky",
	"pluginsTextIsExpanded",
	"eventViewMaxHeight",
	"bgColor",
	"eventManPos",  # FIXME
	"eventManShowDescription",  # FIXME
	"localTzHist",
	"wcal_toolbar_weekNum_negative",
)

confParamsCustomize = (
	"mainWinItems",
	"winControllerButtons",
	"mcalHeight",
	"mcalLeftMargin",
	"mcalTopMargin",
	"mcalTypeParams",
	"mcalGrid",
	"mcalGridColor",
	"wcalHeight",
	"wcalTextSizeScale",
	"wcalItems",
	"wcalGrid",
	"wcalGridColor",
	"wcalPastTextColorEnable_eventsText",
	"wcalPastTextColor_eventsText",
	"wcal_toolbar_mainMenu_icon",
	"wcal_weekDays_width",
	"wcal_weekDays_expand",
	"wcalFont_weekDays",
	"wcalFont_pluginsText",
	"wcal_eventsIcon_width",
	"wcal_eventsText_showDesc",
	"wcal_eventsText_colorize",
	"wcalFont_eventsText",
	"wcal_daysOfMonth_dir",
	"wcalTypeParams",
	"wcal_daysOfMonth_width",
	"wcal_daysOfMonth_expand",
	"wcal_eventsCount_width",
	"wcal_eventsCount_expand",
	"wcalFont_eventsBox",
	"wcal_moonStatus_width",
	"dcalHeight",
	"dcalButtonsEnable",
	# "dcalButtons",
	"dcalTypeParams",
	"dcalWeekdayParams",
	"dcalWinBackgroundColor",
	"dcalWinButtonsEnable",
	# "dcalWinButtons",
	"dcalWinTypeParams",
	"dcalWinWeekdayParams",
	"pluginsTextInsideExpander",
	"seasonPBar_southernHemisphere",
	"wcal_moonStatus_southernHemisphere",
	"statusBarDatesReverseOrder",
	"statusBarDatesColorEnable",
	"statusBarDatesColor",
	"ud__wcalToolbarData",
	"ud__mainToolbarData",
)


def loadConf() -> None:
	loadModuleJsonConf(__name__)
	loadJsonConf(__name__, confPathCustomize)
	loadJsonConf(__name__, confPathLive)


def saveConf() -> None:
	saveModuleJsonConf(__name__)


def saveConfCustomize() -> None:
	saveJsonConf(__name__, confPathCustomize, confParamsCustomize)


def saveLiveConf() -> None:  # rename to saveConfLive FIXME
	if core.debugMode:
		print("saveLiveConf", winX, winY, winWidth)
	saveJsonConf(__name__, confPathLive, confParamsLive)


def saveLiveConfLoop() -> None:  # rename to saveConfLiveLoop FIXME
	tm = now()
	if tm - lastLiveConfChangeTime > saveLiveConfDelay:
		saveLiveConf()
		return False  # Finish loop
	return True  # Continue loop


#######################################################

def parseDroppedDate(text) -> Tuple[int, int, int]:
	part = text.split("/")
	if len(part) == 3:
		try:
			part[0] = numDecode(part[0])
			part[1] = numDecode(part[1])
			part[2] = numDecode(part[2])
		except:
			myRaise(__file__)
			return None
		maxPart = max(part)
		if maxPart > 999:
			minMax = (
				(1000, 2100),
				(1, 12),
				(1, 31),
			)
			formats = (
				[0, 1, 2],
				[1, 2, 0],
				[2, 1, 0],
			)
			for format in formats:
				for i in range(3):
					valid = True
					f = format[i]
					if not (minMax[f][0] <= part[i] <= minMax[f][1]):
						valid = False
						break
				if valid:
					# "format" must be list because we use method "index"
					year = part[format.index(0)]
					month = part[format.index(1)]
					day = part[format.index(2)]
					break
		else:
			valid = 0 <= part[0] <= 99 and \
				1 <= part[1] <= 12 and \
				1 <= part[2] <= 31
			###
			year = 2000 + part[0]  # FIXME
			month = part[1]
			day = part[2]
		if not valid:
			return None
	else:
		return None
	# FIXME: when drag from a persian GtkCalendar with format %y/%m/%d
	#if year < 100:
	#	year += 2000
	return (year, month, day)


def dictsTupleConfStr(data: Sequence[Dict]) -> str:
	n = len(data)
	st = "("
	for i in range(n):
		d = data[i].copy()
		st += "\n{"
		for k in d.keys():
			v = d[k]
			if isinstance(k, str):
				ks = "\'%s\'" % k
			else:
				ks = str(k)
			if isinstance(v, str):
				vs = "\'%s\'" % v
			else:
				vs = str(v)
			st += "%s:%s, " % (ks, vs)
		if i == n - 1:
			st = st[:-2] + "})"
		else:
			st = st[:-2] + "},"
	return st


def checkNeedRestart() -> bool:
	for key in needRestartPref.keys():
		if needRestartPref[key] != eval(key):
			print("\"%s\", \"%s\", \"%s\"" % (
				key,
				needRestartPref[key],
				eval(key)
			))
			return True
	return False


def dayOpenEvolution(arg: Any = None) -> None:
	from subprocess import Popen
	# y, m, d = jd_to(cell.jd-1, core.GREGORIAN)
	# in gnome-cal opens prev day! why??
	y, m, d = cell.dates[core.GREGORIAN]
	Popen(
		"LANG=en_US.UTF-8 evolution calendar:///?startdate=%.4d%.2d%.2d"
		% (y, m, d),
		shell=True,
	)  # FIXME
	# "calendar:///?startdate=%.4d%.2d%.2dT120000Z"%(y, m, d)
	# What "Time" pass to evolution?
	# like gnome-clock: T193000Z (19:30:00) / Or ignore "Time"
	# evolution calendar:///?startdate=$(date +"%Y%m%dT%H%M%SZ")


def dayOpenSunbird(arg: Any = None):
	from subprocess import Popen
	# does not work on latest version of Sunbird, FIXME
	# and Sunbird seems to be a dead project
	# Opens previous day in older version
	y, m, d = cell.dates[core.GREGORIAN]
	Popen(
		"LANG=en_US.UTF-8 sunbird -showdate %.4d/%.2d/%.2d"
		% (y, m, d),
		shell=True,
	)

# How do this with KOrginizer? FIXME

#######################################################################


class Cell(CellType):
	"""
	status and information of a cell
	"""
	# ocTimeMax = 0
	# ocTimeCount = 0
	# ocTimeSum = 0
	def __init__(self, jd: int):
		self.eventsData = [] # type: List[Dict]
		# self.eventsDataIsSet = False  # not used
		self.pluginsText = ""
		###
		self.jd = jd
		date = core.jd_to_primary(jd)
		self.year, self.month, self.day = date
		self.weekDay = core.jwday(jd)
		self.weekNum = core.getWeekNumber(self.year, self.month, self.day)
		# self.weekNumNeg = self.weekNum+1 - core.getYearWeeksCount(self.year)
		self.weekNumNeg = self.weekNum - int(
			calTypes.primaryModule().avgYearLen / 7
		)
		self.holiday = (self.weekDay in core.holidayWeekDays)
		###################
		self.dates = [
			date if calType == calTypes.primary else jd_to(jd, calType)
			for calType in range(len(calTypes))
		]
		"""
		self.dates = dict([
			(
				calType, date if calType==calTypes.primary else jd_to(jd, calType)
			)
			for calType in calTypes.active
		])
		"""
		###################
		for k in core.plugIndex:
			plug = core.allPlugList[k]
			if plug:
				try:
					plug.updateCell(self)
				except:
					myRaiseTback()
		###################
		# t0 = now()
		self.eventsData = event_lib.getDayOccurrenceData(
			jd,
			eventGroups,
		)  # here? FIXME
		"""
		self.eventsData is a list, each item is a dictionary
		with these keys and type:
			time: str (time descriptive string)
			time_epoch: int (epoch time)
			is_allday: bool
			text: tuple of text lines
			icon: str (icon path)
			color: tuple (r, g, b) or (r, g, b, a)
			ids: tuple (gid, eid)
			show: tuple of 3 bools (showInDCal, showInWCal, showInMCal)
			showInStatusIcon: bool
		"""
		# dt = now() - t0
		# Cell.ocTimeSum += dt
		# Cell.ocTimeCount += 1
		# Cell.ocTimeMax = max(Cell.ocTimeMax, dt)

	def format(
		self,
		compiledFmt: CompiledTimeFormat,
		calType: Optional[int] = None,
		tm: Optional[Tuple[int, int, int]] = None,
	):
		if calType is None:
			calType = calTypes.primary
		if tm is None:
			tm = (0, 0, 0)
		pyFmt, funcs = compiledFmt
		return pyFmt % tuple(f(self, calType, tm) for f in funcs)

	def getDate(self, calType: int) -> Tuple[int, int, int]:
		return self.dates[calType]

	def inSameMonth(self, other: CellType) -> bool:
		return self.getDate(calTypes.primary)[:2] == \
			other.getDate(calTypes.primary)[:2]

	def getEventIcons(self, showIndex: int) -> List[str]:
		iconList = []
		for item in self.eventsData:
			if not item["show"][showIndex]:
				continue
			icon = item["icon"]
			if icon and icon not in iconList:
				iconList.append(icon)
		return iconList

	def getDayEventIcons(self) -> List[str]:
		return self.getEventIcons(0)

	def getWeekEventIcons(self) -> List[str]:
		return self.getEventIcons(1)

	def getMonthEventIcons(self) -> List[str]:
		return self.getEventIcons(2)


class CellCache:
	def __init__(self) -> None:
		# a mapping from julan_day to Cell instance
		self.jdCells = {} # type: Dict[int, CellType]
		self.plugins = {} # type: Dict[str, Tuple[Callable[[CellType], None], Callable[[CellCache, ...], List[CellType]]]]
		self.weekEvents = {} # type Dict[int, List[Dict]]

	def clear(self) -> None:
		global cell, todayCell
		self.jdCells = {}
		self.weekEvents = {}
		cell = self.getCell(cell.jd)
		todayCell = self.getCell(todayCell.jd)

	def registerPlugin(
		self,
		name: str,
		setParamsCallable: Callable[[CellType], None],
		getCellGroupCallable: "Callable[[CellCache, ...], List[CellType]]", # FIXME: ...
		# `...` is `absWeekNumber` for weekCal, and `year, month` for monthCal
	):
		"""
			setParamsCallable(cell): cell.attr1 = value1 ....
			getCellGroupCallable(cellCache, *args): return cell_group
				call cellCache.getCell(jd) inside getCellGroupFunc
		"""
		self.plugins[name] = (
			setParamsCallable,
			getCellGroupCallable,
		)
		for localCell in self.jdCells.values():
			setParamsCallable(localCell)

	def getCell(self, jd: int) -> CellType:
		c = self.jdCells.get(jd)
		if c is not None:
			return c
		return self.buildCell(jd)

	def getTmpCell(self, jd: int) -> CellType:
		# don't keep, no eventsData, no plugin params
		c = self.jdCells.get(jd)
		if c is not None:
			return c
		return Cell(jd)

	def getCellByDate(self, y: int, m: int, d: int) -> CellType:
		return self.getCell(core.primary_to_jd(y, m, d))

	def getTodayCell(self) -> CellType:
		return self.getCell(core.getCurrentJd())

	def buildCell(self, jd: int) -> CellType:
		localCell = Cell(jd)
		for pluginData in self.plugins.values():
			pluginData[0](localCell)
		self.jdCells[jd] = localCell
		cleanCacheDict(self.jdCells, maxDayCacheSize, jd)
		return localCell

	def getCellGroup(self, pluginName: int, *args) -> List[CellType]:
		return self.plugins[pluginName][1](self, *args)

	def getWeekData(self, absWeekNumber: int) -> Tuple[List[CellType], List[Dict]]:
		cells = self.getCellGroup("WeekCal", absWeekNumber)
		wEventData = self.weekEvents.get(absWeekNumber)
		if wEventData is None:
			wEventData = event_lib.getWeekOccurrenceData(
				absWeekNumber,
				eventGroups,
			)
			cleanCacheDict(self.weekEvents, maxWeekCacheSize, absWeekNumber)
			self.weekEvents[absWeekNumber] = wEventData
		return cells, wEventData

	# def getMonthData(self, year, month):  # needed? FIXME


def changeDate(year: int, month: int, day: int, calType: Optional[int] = None) -> None:
	global cell
	if calType is None:
		calType = calTypes.primary
	cell = cellCache.getCell(core.to_jd(year, month, day, calType))


def gotoJd(jd: int) -> None:
	global cell
	cell = cellCache.getCell(jd)


def jdPlus(plus: int = 1) -> None:
	global cell
	cell = cellCache.getCell(cell.jd + plus)


def getMonthPlus(tmpCell: CellType, plus: int) -> CellType:
	year, month = core.monthPlus(tmpCell.year, tmpCell.month, plus)
	day = min(tmpCell.day, core.getMonthLen(year, month, calTypes.primary))
	return cellCache.getCellByDate(year, month, day)


def monthPlus(plus: int = 1) -> None:
	global cell
	cell = getMonthPlus(cell, plus)


def yearPlus(plus: int = 1) -> None:
	global cell
	year = cell.year + plus
	month = cell.month
	day = min(cell.day, core.getMonthLen(year, month, calTypes.primary))
	cell = cellCache.getCellByDate(year, month, day)


def getFont(scale=1.0, familiy=True) -> Tuple[Optional[str], bool, bool, float]:
	(
		name,
		bold,
		underline,
		size,
	) = fontCustom if fontCustomEnable else fontDefaultInit
	return [
		name if familiy else None,
		bold,
		underline,
		size * scale,
	]


def getParamsFont(params: Dict) -> Optional[Tuple[str, bool, bool, float]]:
	font = params.get("font")
	if not font:
		return None
	if font[0] is None:
		font = list(font) # copy
		font[0] = getFont()[0]
	return font


def initFonts(fontDefaultNew: Tuple[str, bool, bool, float]) -> None:
	global fontDefault, fontCustom, mcalTypeParams
	fontDefault = fontDefaultNew
	if not fontCustom:
		fontCustom = fontDefault
	########
	###
	if mcalTypeParams[0]["font"] is None:
		mcalTypeParams[0]["font"] = getFont(1.0, familiy=False)
	###
	for item in mcalTypeParams[1:]:
		if item["font"] is None:
			item["font"] = getFont(0.6, familiy=False)
	######
	if dcalTypeParams[0]["font"] is None:
		dcalTypeParams[0]["font"] = getFont(10.0, familiy=False)
	###
	for item in dcalTypeParams[1:]:
		if item["font"] is None:
			item["font"] = getFont(3.0, familiy=False)
	######
	if dcalWinTypeParams[0]["font"] is None:
		dcalWinTypeParams[0]["font"] = getFont(5.0, familiy=False)
	###
	for item in dcalWinTypeParams[1:]:
		if item["font"] is None:
			item["font"] = getFont(2.0, familiy=False)
	######
	if dcalWeekdayParams["font"] is None:
		dcalWeekdayParams["font"] = getFont(1.0, familiy=False)
	if dcalWinWeekdayParams["font"] is None:
		dcalWinWeekdayParams["font"] = getFont(1.0, familiy=False)


def getHolidaysJdList(startJd: int, endJd: int) -> List[int]:
	jdList = []
	for jd in range(startJd, endJd):
		tmpCell = cellCache.getTmpCell(jd)
		if tmpCell.holiday:
			jdList.append(jd)
	return jdList


######################################################################

def checkMainWinItems() -> None:
	global mainWinItems
	# print(mainWinItems)
	# cleaning and updating mainWinItems
	names = {
		name
		for (name, i) in mainWinItems
	}
	defaultNames = {
		name
		for (name, i) in mainWinItemsDefault
	}
	# print(mainWinItems)
	# print(sorted(names))
	# print(sorted(defaultNames))
	#####
	# removing items that are no longer supported
	mainWinItems, mainWinItemsTmp = [], mainWinItems
	for name, enable in mainWinItemsTmp:
		if name in defaultNames:
			mainWinItems.append((name, enable))
	#####
	# adding items newly added in this version, this is for user"s convenience
	newNames = defaultNames.difference(names)
	# print("mainWinItems: newNames =", newNames)
	##
	name = "winContronller"
	if name in newNames:
		mainWinItems.insert(0, (name, True))
		newNames.remove(name)
	##
	for name in newNames:
		mainWinItems.append((name, False))  # FIXME


def deleteEventGroup(group: event_lib.EventGroup) -> None:
	eventGroups.moveToTrash(group, eventTrash)


def moveEventToTrash(group: event_lib.EventGroup, event: event_lib.Event) -> int:
	eventIndex = group.remove(event)
	group.save()
	eventTrash.insert(0, event)  # or append? FIXME
	eventTrash.save()
	return eventIndex


def moveEventToTrashFromOutside(group: event_lib.EventGroup, event: event_lib.Event) -> None:
	global reloadGroups, reloadTrash
	moveEventToTrash(group, event)
	reloadGroups.append(group.id)
	reloadTrash = True


def getEvent(groupId: int, eventId: int) -> event_lib.Event:
	return eventGroups[groupId][eventId]


def duplicateGroupTitle(group: event_lib.EventGroup) -> None:
	title = group.title
	titleList = [g.title for g in eventGroups]
	parts = title.split("#")
	try:
		index = int(parts[-1])
		title = "#".join(parts[:-1])
	except:
		# myRaise()
		index = 1
	index += 1
	while True:
		newTitle = title + "#%d" % index
		if newTitle not in titleList:
			group.title = newTitle
			return
		index += 1


def init() -> None:
	global todayCell, cell, fs, eventAccounts, eventGroups, eventTrash
	core.init()

	fs = event_lib.DefaultFileSystem(confDir)
	event_lib.init(fs)
	# Load accounts, groups and trash? FIXME
	eventAccounts = event_lib.EventAccountsHolder.load(fs)
	eventGroups = event_lib.EventGroupsHolder.load(fs)
	eventTrash = event_lib.EventTrash.load(fs)
	####
	todayCell = cell = cellCache.getTodayCell()  # FIXME


def withFS(obj: "SObj") -> "SObj":
	obj.fs = fs
	return obj


######################################################################

localTzHist = [
	str(core.localTz),
]

shownCals = []	# FIXME

mcalTypeParams = [
	{
		"pos": (0, -2),
		"font": None,
		"color": (220, 220, 220),
	},
	{
		"pos": (18, 5),
		"font": None,
		"color": (165, 255, 114),
	},
	{
		"pos": (-18, 4),
		"font": None,
		"color": (0, 200, 205),
	},
]

wcalTypeParams = [
	{"font": None},
	{"font": None},
	{"font": None},
]

dcalTypeParams = [  # FIXME
	{
		"pos": (0, -12),
		"font": None,
		"color": (220, 220, 220),
	},
	{
		"pos": (125, 30),
		"font": None,
		"color": (165, 255, 114),
	},
	{
		"pos": (-125, 24),
		"font": None,
		"color": (0, 200, 205),
	},
]
dcalWeekdayParams = {
	"enable": False,
	"pos": (20, 10),
	"xalign": "right",
	"yalign": "buttom",
	"font": None,
	"color": (0, 200, 205),
}

dcalWinTypeParams = [
	{
		"pos": (0, 5),
		"xalign": "left",
		"yalign": "center",
		"font": None,
		"color": (220, 220, 220),
	},
	{
		"pos": (5, 0),
		"xalign": "right",
		"yalign": "top",
		"font": None,
		"color": (165, 255, 114),
	},
	{
		"pos": (0, 0),
		"xalign": "right",
		"yalign": "buttom",
		"font": None,
		"color": (0, 200, 205),
	},
]
dcalWinWeekdayParams = {
	"enable": False,
	"pos": (20, 10),
	"xalign": "right",
	"yalign": "buttom",
	"font": None,
	"color": (0, 200, 205),
}


def getActiveMonthCalParams():
	return list(zip(
		calTypes.active,
		mcalTypeParams,
	))




################################

tagsDir = join(pixDir, "event")


class TagIconItem:
	def __init__(self, name, desc="", icon="", eventTypes=()):
		self.name = name
		if not desc:
			desc = name.capitalize()
		self.desc = _(desc)
		if icon:
			if not isabs(icon):
				icon = join(tagsDir, icon)
		else:
			iconTmp = join(tagsDir, name) + ".png"
			if isfile(iconTmp):
				icon = iconTmp
		self.icon = icon
		self.eventTypes = eventTypes
		self.usage = 0

	def __repr__(self):
		return "TagIconItem(%r, desc=%r, icon=%r, eventTypes=%r)" % (
			self.name,
			self.desc,
			self.icon,
			self.eventTypes,
		)


eventTags = (
	TagIconItem("birthday", eventTypes=("yearly",)),
	TagIconItem("marriage", eventTypes=("yearly",)),
	TagIconItem("obituary", eventTypes=("yearly",)),
	TagIconItem("note", eventTypes=("dailyNote",)),
	TagIconItem("task", eventTypes=("task",)),
	TagIconItem("alarm"),
	TagIconItem("business"),
	TagIconItem("personal"),
	TagIconItem("favorite"),
	TagIconItem("important"),
	TagIconItem("appointment", eventTypes=("task",)),
	TagIconItem("meeting", eventTypes=("task",)),
	TagIconItem("phone_call", desc="Phone Call", eventTypes=("task",)),
	TagIconItem("university", eventTypes=("task",)),  # FIXME
	TagIconItem("education"),
	TagIconItem("holiday"),
	TagIconItem("travel"),
)


def getEventTagsDict():
	return {
		tagObj.name: tagObj for tagObj in eventTags
	}


eventTagsDesc = {
	t.name: t.desc for t in eventTags
}

###################
fs = None # type: event_lib.FileSystem
eventAccounts = [] # type: List[event_lib.EventAccount]
eventGroups = [] # type: List[event_lib.EventGroup]
eventTrash = None # type: event_lib.EventTrash


def iterAllEvents():  # dosen"t include orphan events
	for group in eventGroups:
		for event in group:
			yield event
	for event in eventTrash:
		yield event


changedGroups = []  # list of groupId"s
reloadGroups = []  # a list of groupId"s that their contents are changed
reloadTrash = False

eventDiff = EventDiff()


# def updateEventTagsUsage():  # FIXME where to use?
#	tagsDict = getEventTagsDict()
#	for tagObj in eventTags:
#		tagObj.usage = 0
#	for event in events:  # FIXME
#		for tag in event.tags:
#			td = tagsDict.get(tag)
#			if td is not None:
#				tagsDict[tag].usage += 1


###################
# BUILD CACHE AFTER SETTING calTypes.primary
maxDayCacheSize = 100  # maximum size of cellCache (days number)
maxWeekCacheSize = 12

cellCache = CellCache()
todayCell = cell = None
###########################
autoLocale = True
logo = join(pixDir, "starcal.png")
###########################
# themeDir = join(rootDir, "themes")
# theme = None

# _________________________ Options _________________________ #

# these 2 are loaded from json
ud__wcalToolbarData = None
ud__mainToolbarData = None

winWidth = 480
mcalHeight = 250
winTaskbar = False
useAppIndicator = True
showDigClockTb = True  # On Toolbar FIXME
showDigClockTr = True  # On Status Icon
####
toolbarIconSizePixel = 24  # used in pyqt ui
####
bgColor = (26, 0, 1, 255)  # or None
bgUseDesk = False
borderColor = (123, 40, 0, 255)
borderTextColor = (255, 255, 255, 255)  # text of weekDays and weekNumbers
# menuBgColor = borderColor ##???????????????
textColor = (255, 255, 255, 255)
menuTextColor = None  # borderTextColor # FIXME
holidayColor = (255, 160, 0, 255)
inactiveColor = (255, 255, 255, 115)
todayCellColor = (0, 255, 0, 50)
##########
cursorOutColor = (213, 207, 0, 255)
cursorBgColor = (41, 41, 41, 255)
cursorDiaFactor = 0.15
cursorRoundingFactor = 0.50
mcalGrid = False
mcalGridColor = (255, 252, 0, 82)
##########
mcalLeftMargin = 30
mcalTopMargin = 30
####################
wcalHeight = 200
wcalTextSizeScale = 0.6  # between 0 and 1
# wcalTextColor = (255, 255, 255)  # FIXME
wcalPadding = 10
wcalGrid = False
wcalGridColor = (255, 252, 0, 82)

wcalPastTextColorEnable_eventsText = False
wcalPastTextColor_eventsText = (100, 100, 100, 50)

wcal_toolbar_mainMenu_icon = "starcal-24.png"
wcal_toolbar_mainMenu_icon_default = wcal_toolbar_mainMenu_icon
wcal_toolbar_weekNum_negative = False
wcal_weekDays_width = 80
wcal_weekDays_expand = False
wcal_eventsCount_width = 80
wcal_eventsCount_expand = False
wcal_eventsIcon_width = 50
wcal_eventsText_showDesc = False
wcal_eventsText_colorize = True
wcal_daysOfMonth_width = 30
wcal_daysOfMonth_expand = False
wcal_daysOfMonth_dir = "ltr"  # ltr/rtl/auto
wcalFont_eventsText = None
wcalFont_weekDays = None
wcalFont_pluginsText = None
wcalFont_eventsBox = None
wcal_moonStatus_width = 48

####################
dcalHeight = 250
dcalButtonsEnable = False
dcalButtons = [
	{
		"imageName": "transform-move.png",
		"onClick": "startMove",
		"x": 0,
		"y": 0,
		"autoDir": False,
	},
	{
		"imageName": "resize-small.png",
		"onClick": "startResize",
		"x": -1,
		"y": -1,
		"autoDir": False,
	},
]

dcalWinX = 0
dcalWinY = 0
dcalWinWidth = 180
dcalWinHeight = 180
dcalWinBackgroundColor = (0, 10, 0)
dcalWinButtonsEnable = True
dcalWinButtons = [
	{
		"imageName": "transform-move.png",
		"onClick": "startMove",
		"x": 0,
		"y": 0,
		"autoDir": False,
	},
	{
		"imageName": "resize-small.png",
		"onClick": "startResize",
		"x": -1,
		"y": -1,
		"autoDir": False,
	},
	{
		"iconName": "gtk-edit",
		"iconSize": 16,
		"onClick": "openCustomize",
		"x": 0,
		"y": -1,
		"autoDir": False,
	},
]

####################

statusBarDatesReverseOrder = False
statusBarDatesColorEnable = False
statusBarDatesColor = (255, 132, 255, 255)

####################

boldYmLabel = True  # apply in Pref FIXME
showYmArrows = True  # apply in Pref FIXME

# delay for shift up/down items of menu for right click on YearLabel
labelMenuDelay = 0.1

####################

statusIconImage = join(rootDir, "status-icons", "dark-green.svg")
statusIconImageHoli = join(rootDir, "status-icons", "dark-red.svg")
(
	statusIconImageDefault,
	statusIconImageHoliDefault,
) = statusIconImage, statusIconImageHoli
statusIconFontFamilyEnable = False
statusIconFontFamily = None
statusIconFixedSizeEnable = False
statusIconFixedSizeWH = (24, 24)
####################
menuActiveLabelColor = "#ff0000"
pluginsTextStatusIcon = False
pluginsTextInsideExpander = True
pluginsTextIsExpanded = True  # effects only if pluginsTextInsideExpander
eventViewMaxHeight = 200
####################
dragGetCalType = core.GREGORIAN   # apply in Pref FIXME
# dragGetDateFormat = "%Y/%m/%d"
dragRecMode = core.GREGORIAN   # apply in Pref FIXME
####################
monthRMenuNum = True
# monthRMenu
winControllerButtons = (
	("sep", True),
	("min", True),
	("max", False),
	("close", True),
	("sep", False),
	("sep", False),
	("sep", False),
)
winControllerSpacing = 0
####################
winKeepAbove = True
winSticky = True
winX = 0
winY = 0
###
fontDefault = ["Sans", False, False, 12]
fontDefaultInit = fontDefault
fontCustom = None
fontCustomEnable = False
#####################
showMain = True  # Open main window on start (or only goto statusIcon)
showDesktopWidget = False # Open desktop widget on start
#####################
mainWinItems = (
	("winContronller", True),
	("toolbar", True),
	("labelBox", True),
	("monthCal", False),
	("weekCal", True),
	("dayCal", False),
	("statusBar", True),
	("seasonPBar", True),
	("yearPBar", False),
	("pluginsText", True),
	("eventDayView", True),
)

mainWinItemsDefault = mainWinItems[:]


wcalItems = (
	("toolbar", True),
	("weekDays", True),
	("pluginsText", True),
	("eventsIcon", True),
	("eventsText", True),
	("daysOfMonth", True),
)

wcalItemsDefault = wcalItems[:]

####################

seasonPBar_southernHemisphere = False
wcal_moonStatus_southernHemisphere = False

####################

ntpServers = (
	"pool.ntp.org",
	"ir.pool.ntp.org",
	"asia.pool.ntp.org",
	"europe.pool.ntp.org",
	"north-america.pool.ntp.org",
	"oceania.pool.ntp.org",
	"south-america.pool.ntp.org",
	"ntp.ubuntu.com",
)


#####################

# change date of a dailyNoteEvent when editing it
# dailyNoteChDateOnEdit = True

eventManPos = (0, 0)
eventManShowDescription = True

#####################

focusTime = 0
lastLiveConfChangeTime = 0


saveLiveConfDelay = 0.5  # seconds
timeout_initial = 200
timeout_repeat = 50


def updateFocusTime(*args):
	global focusTime
	focusTime = now()


########################################################

loadConf()

########################################################

if not isfile(statusIconImage):
	statusIconImage = statusIconImageDefault
if not isfile(statusIconImageHoli):
	statusIconImageHoli = statusIconImageHoliDefault


try:
	localTzHist.remove(str(core.localTz))
except ValueError:
	pass
localTzHist.insert(0, str(core.localTz))
saveLiveConf()


needRestartPref = {}  # Right place? FIXME
for key in (
	"locale_man.lang",
	"locale_man.enableNumLocale",
	"winTaskbar",
	"showYmArrows",
	"useAppIndicator",
):
	needRestartPref[key] = eval(key)

if menuTextColor is None:
	menuTextColor = borderTextColor

##################################

# move to gtk_ud ? FIXME
mainWin = None
prefDialog = None
eventManDialog = None
timeLineWin = None
dayCalWin = None
yearWheelWin = None
weekCalWin = None
