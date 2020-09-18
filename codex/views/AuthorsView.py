from gi.repository import GLib, Gio, Gtk, Gdk, GObject


class AuthorsView(Gtk.Paned):

    def __init__(self, *args, **kwargs):

        kwargs['orientation'] = Gtk.Orientation.HORIZONTAL
        super().__init__(**kwargs)

        scrolled_window = Gtk.ScrolledWindow()
        self.authors_tree = Gtk.TreeView()
        scrolled_window.add(self.authors_tree)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('ID', renderer, text=0)
        self.authors_tree.append_column(column)
        column.set_visible(False)
        column.set_resizable(True)
        column = Gtk.TreeViewColumn('Author', renderer, text=1)
        column.set_sort_column_id(1)
        column.set_resizable(True)
        self.authors_tree.append_column(column)
        column = Gtk.TreeViewColumn('Documents', renderer, text=2)
        column.set_sort_column_id(2)
        column.set_resizable(True)
        self.authors_tree.append_column(column)

        self.pack1(scrolled_window)
