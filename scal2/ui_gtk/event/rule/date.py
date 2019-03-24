#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from scal2 import core
from scal2.locale_man import tr as _
from scal2 import event_lib

from scal2.ui_gtk import *
from scal2.ui_gtk.mywidgets.multi_spin.date import DateButton

class WidgetClass(DateButton):
	def __init__(self, rule):
		self.rule = rule
		DateButton.__init__(self)
	def updateWidget(self):
		self.set_value(self.rule.date)
	def updateVars(self):
		self.rule.date = self.get_value()
	def changeMode(self, mode):
		if mode == self.rule.getMode():
			return
		self.updateVars()
		self.rule.changeMode(mode)
		self.updateWidget()
