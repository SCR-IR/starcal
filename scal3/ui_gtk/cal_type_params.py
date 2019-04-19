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

from scal3.cal_types import calTypes

from scal3.locale_man import tr as _

from scal3 import ui

from scal3.ui_gtk import *


class XAlignComboBox(gtk.ComboBoxText):
	def __init__(self):
		gtk.ComboBoxText.__init__(self)
		###
		self.append_text(_("Left"))
		self.append_text(_("Center"))
		self.append_text(_("Right"))
		self.set_active(1)

	def get(self):
		index = self.get_active()
		if index == 0:
			return "left"
		elif index == 1:
			return "center"
		elif index == 2:
			return "right"
		else:
			print("XAlignComboBox: unexpected index =", index)

	def set(self, value):
		if value == "left":
			self.set_active(0)
		elif value == "center":
			self.set_active(1)
		elif value == "right":
			self.set_active(2)
		else:
			self.set_active(1)

class YAlignComboBox(gtk.ComboBoxText):
	def __init__(self):
		gtk.ComboBoxText.__init__(self)
		###
		self.append_text(_("Top"))
		self.append_text(_("Center"))
		self.append_text(_("Buttom"))
		self.set_active(1)

	def get(self):
		index = self.get_active()
		if index == 0:
			return "top"
		elif index == 1:
			return "center"
		elif index == 2:
			return "buttom"
		else:
			print("YAlignComboBox: unexpected index =", index)

	def set(self, value):
		if value == "top":
			self.set_active(0)
		elif value == "center":
			self.set_active(1)
		elif value == "buttom":
			self.set_active(2)
		else:
			self.set_active(1)

class CalTypeParamBox(gtk.Frame):
	def __init__(self, paramName, cal, index, calType, params, sgroupLabel, hasEnable=False, hasAlign=False):
		from scal3.ui_gtk.mywidgets.multi_spin.float_num import FloatSpinButton
		from scal3.ui_gtk.mywidgets import MyFontButton, MyColorButton
		gtk.Frame.__init__(self)
		self.set_border_width(5)
		self.paramName = paramName
		self.cal = cal
		self.index = index
		self.calType = calType
		self.hasEnable = hasEnable
		self.hasAlign = hasAlign
		####
		module, ok = calTypes[calType]
		if not ok:
			raise RuntimeError("cal type %r not found" % calType)
		####
		if hasEnable:
			self.enableCheck = gtk.CheckButton(label=_(module.desc))
			self.set_label_widget(self.enableCheck)
		else:
			self.set_label(_(module.desc))
		####
		vbox = gtk.VBox()
		vbox.set_border_width(5)
		self.add(vbox)
		###
		hbox = gtk.HBox()
		label = gtk.Label(label=_("Position")+": ")
		pack(hbox, label)
		sgroupLabel.add_widget(label)
		spin = FloatSpinButton(-999, 999, 1)
		self.spinX = spin
		pack(hbox, spin)
		pack(hbox, gtk.Label(label=""), 1, 1)
		spin = FloatSpinButton(-999, 999, 1)
		self.spinY = spin
		pack(hbox, spin)
		pack(hbox, gtk.Label(label=""), 1, 1)
		pack(vbox, hbox)
		####
		if hasAlign:
			hbox = gtk.HBox()
			label = gtk.Label(label=_("Alignment")+": ")
			pack(hbox, label)
			sgroupLabel.add_widget(label)
			##
			self.xalignCombo = XAlignComboBox()
			pack(hbox, self.xalignCombo)
			##
			self.yalignCombo = YAlignComboBox()
			pack(hbox, self.yalignCombo)
			##
			pack(hbox, gtk.Label(label=""), 1, 1)
			pack(vbox, hbox)
		####
		hbox = gtk.HBox()
		label = gtk.Label(label=_("Font")+": ")
		pack(hbox, label)
		sgroupLabel.add_widget(label)
		##
		fontb = MyFontButton(cal)
		self.fontb = fontb
		##
		colorb = MyColorButton()
		self.colorb = colorb
		##
		pack(hbox, colorb)
		pack(hbox, gtk.Label(label=""), 1, 1)
		pack(hbox, fontb)
		pack(vbox, hbox)
		####
		self.set(params)
		####
		self.spinX.connect("changed", self.onChange)
		self.spinY.connect("changed", self.onChange)
		fontb.connect("font-set", self.onChange)
		colorb.connect("color-set", self.onChange)
		if hasEnable:
			self.enableCheck.connect("clicked", self.onChange)
		if hasAlign:
			self.xalignCombo.connect("changed", self.onChange)
			self.yalignCombo.connect("changed", self.onChange)

	def get(self):
		params = {
			"pos": (
				self.spinX.get_value(),
				self.spinY.get_value(),
			),
			"font": self.fontb.get_font_name(),
			"color": self.colorb.get_color(),
		}
		if self.hasEnable:
			params["enable"] = self.enableCheck.get_active()
		if self.hasAlign:
			params["xalign"] = self.xalignCombo.get()
			params["yalign"] = self.yalignCombo.get()
		return params

	def set(self, params):
		self.spinX.set_value(params["pos"][0])
		self.spinY.set_value(params["pos"][1])
		self.fontb.set_font_name(params["font"])
		self.colorb.set_color(params["color"])
		if self.hasEnable:
			self.enableCheck.set_active(params.get("enable", True))
		if self.hasAlign:
			self.xalignCombo.set(params.get("xalign", "center"))
			self.yalignCombo.set(params.get("yalign", "center"))

	def onChange(self, obj=None, event=None):
		typeParams = getattr(ui, self.paramName)
		typeParams[self.index] = self.get()
		self.cal.queue_draw()

