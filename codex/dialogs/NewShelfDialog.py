import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class NewShelfDialog(Gtk.Dialog):

    def __init__(self, parent, message):
        Gtk.Dialog.__init__(self, message, parent, 0,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                             Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.set_default_size(320, 240)
        self.connect("response", self.on_response)

        grid = Gtk.Grid()

        self.name_entry = Gtk.Entry()
        self.description_entry = Gtk.TextView()
        self.description_buffer: Gtk.TextBuffer = self.description_entry.get_buffer()
        frame = Gtk.Frame()
        scroll = Gtk.ScrolledWindow()
        scroll.add(self.description_entry)
        scroll.set_hexpand(True)
        scroll.set_border_width(3)
        frame.add(scroll)

        name_label = Gtk.Label(label='Name')
        desc_label = Gtk.Label(label='Description')
        name_label.set_halign(Gtk.Align.START)
        desc_label.set_halign(Gtk.Align.START)
        name_label.set_padding(10, 0)
        desc_label.set_padding(10, 0)

        grid.attach(name_label, 0, 0, 1, 1)
        grid.attach(self.name_entry, 1, 0, 1, 1)
        grid.attach(desc_label, 0, 1, 1, 1)
        grid.attach(frame, 1, 1, 1, 1)

        box = self.get_content_area()
        box.add(grid)
        self.show_all()

        self.name = None
        self.description = None
        self.selected_response = None

    def on_response(self, dialog, response):

        self.selected_response = response

        if response == Gtk.ResponseType.OK:
            self.name = self.name_entry.get_text()
            self.description = self.description_buffer.get_text(
                self.description_buffer.get_start_iter(),
                self.description_buffer.get_end_iter(),
                True
            )
            print(self.name, self.description)

        self.destroy()