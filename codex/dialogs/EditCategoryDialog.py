from gi.repository import Gtk
from codex.db.models import Category
from codex.db.settings import get_session


class EditCategoryDialog(Gtk.Dialog):

    def __init__(self, parent, message, category: Category = None):
        Gtk.Dialog.__init__(self, message, parent, 0,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                             Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.set_default_size(320, 240)
        self.connect("response", self.on_response)
        self.category = category

        grid = Gtk.Grid()

        self.category_store = Gtk.TreeStore()
        self.category_view = Gtk.TreeView(model=self.category_store)
        self.category_name_entry = Gtk.Entry()

        category_name_label = Gtk.Label(label='Category name')
        parent_category_label = Gtk.Label(label='Parent category (optional)')

        labels = [category_name_label, parent_category_label]
        entries = [self.category_name_entry, self.category_view]

        for i, (label, entry) in enumerate(zip(labels, entries)):
            label.set_halign(Gtk.Align.END)
            label.set_padding(10, 10)
            entry.set_halign(Gtk.Align.START)
            grid.attach(label, 0, i, 1, 1)
            grid.attach(entry, 1, i, 1, 1)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('ID', renderer, text=0)
        self.category_view.append_column(column)
        column.set_visible(False)
        column.set_resizable(True)
        column = Gtk.TreeViewColumn('Category', renderer, text=1)
        column.set_sort_column_id(1)
        column.set_resizable(True)
        self.category_view.append_column(column)

        box = self.get_content_area()
        box.add(grid)
        self.show_all()

        self.category_id = None

        if self.category:
            self.category_name_entry.set_text(self.category.name)

        self.selected_response = None

    def load_data(self):

        session = get_session()
        if self.category:
            descendants = [category.id for category in self.category.get_descendants()]
            categories = session.query(Category).filter(
                Category.id != self.category.id
            ).filter(
                ~Category.id._in(descendants)
            ).all()

            for category in categories:
                self.category_store.append()

    def on_response(self, dialog, response):

        self.selected_response = response

        if response == Gtk.ResponseType.OK:
            if not self.author:
                self.author = Author()

            self.author.first_name = self.first_name_entry.get_text()
            self.author.middle_name = self.middle_name_entry.get_text()
            self.author.last_name = self.last_name_entry.get_text()

        self.destroy()
