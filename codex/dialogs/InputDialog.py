import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class InputDialog(Gtk.Dialog):

    def __init__(self, parent, message):
        Gtk.Dialog.__init__(self, message, parent, 0,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                             Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.set_default_size(250, 100)

        self.entry = Gtk.Entry()
        box = self.get_content_area()
        box.add(self.entry)
        self.show_all()