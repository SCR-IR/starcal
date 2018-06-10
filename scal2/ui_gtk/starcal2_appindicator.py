#!/usr/bin/env python2
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

import sys
import atexit
import os
from os.path import dirname
sys.path.insert(0, dirname(dirname(dirname(__file__))))

from scal2.path import *
from scal2.utils import myRaise
from scal2 import core
from scal2 import locale_man
from scal2.locale_man import tr as _

from scal2.ui_gtk import *
from scal2.ui_gtk.utils import (
	CopyLabelMenuItem,
	get_pixbuf_hash,
)

import appindicator

class IndicatorStatusIconWrapper(appindicator.Indicator):
	imNamePrefix = APP_NAME + '-indicator-%s-' % os.getuid()
	def __init__(self, mainWin):
		self.mainWin = mainWin
		appindicator.Indicator.__init__(
			self,
			'starcal2',## app id
			'starcal2',## icon
			appindicator.CATEGORY_APPLICATION_STATUS,
		)
		self.set_status(appindicator.STATUS_ACTIVE)
		#self.set_attention_icon("new-messages-red")
		######
		atexit.register(self.cleanup)
		######
		self.create_menu()
		self.imPath = ''
	'''
	def create_menu_simple(self):
		menu = gtk.Menu()
		###
		for item in [self.mainWin.getMainWinMenuItem()] + self.mainWin.getStatusIconPopupItems():
			item.show()
			menu.add(item)
		###
		#if locale_man.rtl:
			#menu.set_direction(gtk.TEXT_DIR_RTL)
		self.set_menu(menu)
	'''
	def create_menu(self):
		menu = gtk.Menu()
		####
		for line in self.mainWin.getStatusIconTooltip().split('\n'):
			item = CopyLabelMenuItem(line)
			item.show()
			menu.append(item)
		####
		item = self.mainWin.getMainWinMenuItem()
		item.show()
		menu.append(item)
		####
		submenu = gtk.Menu()
		for item in self.mainWin.getStatusIconPopupItems():
			item.show()
			submenu.add(item)
		sitem = gtk.MenuItem(label=_('More'))
		sitem.set_submenu(submenu)
		sitem.show()
		menu.append(sitem)
		self.set_menu(menu)
	def set_from_file(self, fpath):
		self.set_icon('')
		self.set_icon(fpath)
		self.create_menu()
	def set_from_pixbuf(self, pbuf):
		## https://bugs.launchpad.net/ubuntu/+source/indicator-application/+bug/533439
		#pbuf.scale_simple(22, 22, gtk.gdk.INTERP_HYPER)
		fname = self.imNamePrefix + get_pixbuf_hash(pbuf)
		# to make the filename unique, otherwise it won't change in KDE Plasma
		fpath = join(tmpDir, fname + '.png')
		self.imPath = fpath
		pbuf.save(fpath, 'png')
		self.set_from_file(fpath)
	def cleanup(self):
		for fname in os.listdir(tmpDir):
			if not fname.startswith(self.imNamePrefix):
				continue
			try:
				os.remove(join(tmpDir, fname))
			except:
				myRaise()
	is_embedded = lambda self: True ## FIXME
	def set_visible(self, visible):## FIXME
		pass
	def set_tooltip_text(self, text):
		#self.set_label_guide(text)
		pass



