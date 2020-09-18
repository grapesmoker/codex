from gi.repository import Gtk
from codex.db.models import Author


class EditAuthorDialog(Gtk.Dialog):

    def __init__(self, parent, message, author: Author = None):
        Gtk.Dialog.__init__(self, message, parent, 0,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                             Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.set_default_size(320, 240)
        self.connect("response", self.on_response)
        self.author = author

        grid = Gtk.Grid()

        self.first_name_entry = Gtk.Entry()
        self.middle_name_entry = Gtk.Entry()
        self.last_name_entry = Gtk.Entry()

        first_name_label = Gtk.Label(label='First name')
        middle_name_label = Gtk.Label(label='Middle name')
        last_name_label = Gtk.Label(label='Last name')

        labels = [first_name_label, middle_name_label, last_name_label]
        entries = [self.first_name_entry, self.middle_name_entry, self.last_name_entry]

        for i, (label, entry) in enumerate(zip(labels, entries)):
            label.set_halign(Gtk.Align.END)
            label.set_padding(10, 10)
            entry.set_halign(Gtk.Align.START)
            grid.attach(label, 0, i, 1, 1)
            grid.attach(entry, 1, i, 1, 1)

        box = self.get_content_area()
        box.add(grid)
        self.show_all()

        self.author_id = None
        self.first_name = None
        self.middle_name = None
        self.last_name = None

        if self.author:
            self.first_name_entry.set_text(author.first_name)
            self.middle_name_entry.set_text(author.middle_name)
            self.last_name_entry.set_text(author.last_name)

        self.selected_response = None

    def on_response(self, dialog, response):

        self.selected_response = response

        if response == Gtk.ResponseType.OK:
            if not self.author:
                self.author = Author()

            self.author.first_name = self.first_name_entry.get_text()
            self.author.middle_name = self.middle_name_entry.get_text()
            self.author.last_name = self.last_name_entry.get_text()

        self.destroy()
