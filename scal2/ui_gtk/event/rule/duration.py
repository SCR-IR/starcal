#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from scal2 import core
from scal2.locale_man import tr as _
from scal2 import event_lib

from scal2.ui_gtk import *
from scal2.ui_gtk.event import common


class WidgetClass(common.DurationInputBox):
	def __init__(self, rule):
		self.rule = rule
		common.DurationInputBox.__init__(self)
	def updateWidget(self):
		self.setDuration(self.rule.value, self.rule.unit)
	def updateVars(self):
		self.rule.value, self.rule.unit = self.getDuration()

