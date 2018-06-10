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
import os
from os.path import join, isabs
from subprocess import Popen

from scal2.utils import myRaise
from scal2.utils import toStr
from scal2.json_utils import *
from scal2.path import pixDir, rootDir
from scal2.cal_types import calTypes
from scal2 import core
from scal2.locale_man import tr as _
from scal2 import ui

from gobject import timeout_add

from scal2.ui_gtk import *



def hideList(widgets):
	for w in widgets:
		w.hide()

def showList(widgets):
	for w in widgets:
		w.show()


def set_tooltip(widget, text):
	try:
		widget.set_tooltip_text(text)## PyGTK 2.12 or above
	except AttributeError:
		try:
			widget.set_tooltip(gtk.Tooltips(), text)
		except:
			myRaise(__file__)

buffer_get_text = lambda b: b.get_text(b.get_start_iter(), b.get_end_iter())

def setClipboard(text, clipboard=None):
	if not clipboard:
		clipboard = gtk.clipboard_get(gdk.SELECTION_CLIPBOARD)
	text = toStr(text)
	clipboard.set_text(text)
	#clipboard.store() ## ?????? No need!

def imageFromFile(path):## the file must exist
	if not isabs(path):
		path = join(pixDir, path)
	im = gtk.Image()
	try:
		im.set_from_file(path)
	except:
		myRaise()
	return im

def pixbufFromFile(path):## the file may not exist
	if not path:
		return None
	if not isabs(path):
		path = join(pixDir, path)
	try:
		return gdk.pixbuf_new_from_file(path)
	except:
		myRaise()
		return None

toolButtonFromStock = lambda stock, size: gtk.ToolButton(gtk.image_new_from_stock(stock, size))


def labelStockMenuItem(label, stock=None, func=None, *args):
	item = gtk.ImageMenuItem(_(label))
	if stock:
		item.set_image(gtk.image_new_from_stock(stock, gtk.ICON_SIZE_MENU))
	if func:
		item.connect('activate', func, *args)
	return item

def labelImageMenuItem(label, image, func=None, *args):
	item = gtk.ImageMenuItem(_(label))
	item.set_image(imageFromFile(image))
	if func:
		item.connect('activate', func, *args)
	return item

def labelMenuItem(label, func=None, *args):
	item = gtk.MenuItem(_(label))
	if func:
		item.connect('activate', func, *args)
	return item

getStyleColor = lambda widget, state=gtk.STATE_NORMAL:\
	widget.style.base[state]


def modify_bg_all(widget, state, gcolor):
	print(widget.__class__.__name__)
	widget.modify_bg(state, gcolor)
	try:
		children = widget.get_children()
	except AttributeError:
		pass
	else:
		for child in children:
			modify_bg_all(child, state, gcolor)


rectangleContainsPoint = lambda r, x, y: r.x <= x < r.x + r.width and r.y <= y < r.y + r.height

def dialog_add_button(dialog, stock, label, resId, onClicked=None, tooltip=''):
	b = dialog.add_button(stock, resId)
	if ui.autoLocale:
		if label:
			b.set_label(label)
		b.set_image(gtk.image_new_from_stock(stock, gtk.ICON_SIZE_BUTTON))
	if onClicked:
		b.connect('clicked', onClicked)
	if tooltip:
		set_tooltip(b, tooltip)
	return b

def confirm(msg, parent=None):
	win = gtk.MessageDialog(
		parent=parent,
		flags=0,
		type=gtk.MESSAGE_INFO,
		buttons=gtk.BUTTONS_NONE,
		message_format=msg,
	)
	dialog_add_button(win, gtk.STOCK_CANCEL, _('_Cancel'), gtk.RESPONSE_CANCEL)
	dialog_add_button(win, gtk.STOCK_OK, _('_OK'), gtk.RESPONSE_OK)
	ok = win.run() == gtk.RESPONSE_OK
	win.destroy()
	return ok

def showMsg(msg, parent, msg_type):
	win = gtk.MessageDialog(
		parent=parent,
		flags=0,
		type=msg_type,
		buttons=gtk.BUTTONS_NONE,
		message_format=msg,
	)
	dialog_add_button(win, gtk.STOCK_CLOSE, _('_Close'), gtk.RESPONSE_OK)
	win.run()
	win.destroy()

def showError(msg, parent=None):
	showMsg(msg, parent, gtk.MESSAGE_ERROR)

def showInfo(msg, parent=None):
	showMsg(msg, parent, gtk.MESSAGE_INFO)

def openWindow(win):
	win.set_keep_above(ui.winKeepAbove)
	win.present()

def get_menu_width(menu):
	return menu.size_request()[0]


def get_pixbuf_hash(pbuf):
	import hashlib
	md5 = hashlib.md5()

	def save_func(chunkBytes, unknown):
		md5.update(chunkBytes)
		return True

	pbuf.save_to_callback(
		save_func,
		'bmp',  # type, name of file format
		{},  # options, dict
		None,  # user_data
	)
	return md5.hexdigest()


class IdComboBox(gtk.ComboBox):
	def set_active(self, _id):
		ls = self.get_model()
		for i in range(len(ls)):
			if ls[i][0]==_id:
				gtk.ComboBox.set_active(self, i)
				return
	def get_active(self):
		i = gtk.ComboBox.get_active(self)
		if i is None:
			return
		try:
			return self.get_model()[i][0]
		except IndexError:
			return

class CopyLabelMenuItem(gtk.MenuItem):
	def __init__(self, label):
		gtk.MenuItem.__init__(self, label=label, use_underline=False)
		self.connect('activate', self.on_activate)
	def on_activate(self, item):
		setClipboard(self.get_property('label'))


if __name__=='__main__':
	diolog = gtk.Dialog()
	w = TimeZoneComboBoxEntry()
	pack(diolog.vbox, w)
	diolog.vbox.show_all()
	diolog.run()


