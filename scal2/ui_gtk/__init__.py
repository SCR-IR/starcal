__all__ = [
	'gtk',
	'gdk',
	'pack',
	'TWO_BUTTON_PRESS',
]

import gtk
from gtk import gdk

def pack(box, child, expand=False, fill=False, padding=0):
	if isinstance(box, gtk.Box):
		box.pack_start(child, expand, fill, padding)
	elif isinstance(box, gtk.CellLayout):
		box.pack_start(child, expand)
	else:
		raise TypeError('pack: unkown type %s'%type(box))

TWO_BUTTON_PRESS = getattr(gdk, '_2BUTTON_PRESS')

