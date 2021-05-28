from gi.repository import Gtk
from codex.db.models import Author
from codex.db.settings import get_session


class SelectExistingCategoryDialog(Gtk.Dialog):

    def __init__(self, parent, categories, *args, **kwargs):

        Gtk.Dialog.__init__(self, 'Select category', parent, 0,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                             Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.category_store = Gtk.TreeStore()
        self.categories = categories
        self.connect('response', self.on_response)

        content: Gtk.Box = self.get_content_area()
        self.category_view = Gtk.TreeView(model=self.category_store)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.add(self.category_view)
        content.add(scrolled_window)
        self.load_data()

        self.selected_category = None
        self.show_all()

    def load_data(self):

        self.category_store.clear()

        def insert_category(parent, category):
            parent_iter = self.category_store.insert(parent, -1, [category.id, category.name])
            for child in category.subcategories:
                insert_category(parent_iter, child)

        for category in self.categories:
            if category.parent_id is None:
                insert_category(None, category)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Id', renderer, text=0)
        self.category_view.append_column(column)
        column.set_visible(False)
        column = Gtk.TreeViewColumn('Category', renderer, text=1)
        self.category_view.append_column(column)

    def on_response(self, dialog, response):

        if response == Gtk.ResponseType.OK:

            selection: Gtk.TreeSelection = self.category_view.get_selection()
            model, tree_iter = selection.get_selected()
            if tree_iter:
                session = get_session()
                category_id = model[tree_iter][0]
                self.selected_category = session.query(Author).get(category_id)

        dialog.destroy()