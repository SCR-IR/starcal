#!/usr/bin/env python3
__all__ = [
	"gtk",
	"gdk",
	"GdkPixbuf",
	"pack",
	"TWO_BUTTON_PRESS",
	"MenuItem",
	"ImageMenuItem",
	"getScrollValue",
	"timeout_add",
	"timeout_add_seconds",
	"source_remove",
]

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("PangoCairo", "1.0")

from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from gi.repository import GdkPixbuf

try:
	from gi.repository.GLib import timeout_add, timeout_add_seconds, source_remove
except ImportError:
	from gi.repository.GObject import timeout_add, timeout_add_seconds, source_remove


TWO_BUTTON_PRESS = getattr(gdk.EventType, "2BUTTON_PRESS")


def pack(box, child, expand=False, fill=False, padding=0):
	if isinstance(box, gtk.Box):
		box.pack_start(child, expand, fill, padding)
	elif isinstance(box, gtk.CellLayout):
		box.pack_start(child, expand)
	else:
		raise TypeError("pack: unkown type %s" % type(box))


def getScrollValue(gevent):
	"""
	return value is either "up" or "down"
	"""
	value = gevent.direction.value_nick
	if value == "smooth":  # happens *sometimes* in PyGI (Gtk3)
		if gevent.delta_y < 0:  # -1.0 (up)
			value = "up"
		else:
			# most of the time delta_y=1.0, but sometimes 0.0, why?!
			# both mean "down" though
			value = "down"
	return value


class MenuItem(gtk.MenuItem):
	def __init__(self, *args, **kwargs):
		gtk.MenuItem.__init__(self, *args, **kwargs)
		self.set_use_underline(True)


class ImageMenuItem(gtk.ImageMenuItem):
	def __init__(self, *args, **kwargs):
		gtk.ImageMenuItem.__init__(self, *args, **kwargs)
		self.set_use_underline(True)
