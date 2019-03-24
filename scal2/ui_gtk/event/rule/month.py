#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from scal2 import core
from scal2 import locale_man
from scal2.locale_man import tr as _
from scal2 import event_lib

from scal2.ui_gtk import *
from scal2.ui_gtk.utils import set_tooltip


class WidgetClass(gtk.HBox):
	def __init__(self, rule):
		self.rule = rule
		###
		gtk.HBox.__init__(self)
		###
		self.buttons = []
		mode = self.rule.getMode()
		for i in range(12):
			b = gtk.ToggleButton(_(i+1))
			set_tooltip(b, locale_man.getMonthName(mode, i+1))
			pack(self, b)
			self.buttons.append(b)
	def updateWidget(self):
		monthList = self.rule.getValuesPlain()
		for i in range(12):
			self.buttons[i].set_active((i+1) in monthList)
	def updateVars(self):
		monthList = []
		for i in range(12):
			if self.buttons[i].get_active():
				monthList.append(i+1)
		self.rule.setValuesPlain(monthList)
	def changeMode(self, mode):
		if mode == self.rule.getMode():
			return
		for i in range(12):
			set_tooltip(
				self.buttons[i],
				locale_man.getMonthName(mode, i + 1),
			)
