from gi.repository import GLib, Gio, Gtk, Gdk, GObject


class CategoriesView(Gtk.Paned):

    def __init__(self, *args, **kwargs):

        kwargs['orientation'] = Gtk.Orientation.HORIZONTAL
        super().__init__(**kwargs)

        scrolled_window = Gtk.ScrolledWindow()
        self.categories_tree = Gtk.TreeView()
        scrolled_window.add(self.categories_tree)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('ID', renderer, text=0)
        self.categories_tree.append_column(column)
        column.set_visible(False)
        column.set_resizable(True)
        column = Gtk.TreeViewColumn('Category', renderer, text=1)
        column.set_sort_column_id(1)
        column.set_resizable(True)
        self.categories_tree.append_column(column)

        self.pack1(scrolled_window)

    def categories_context_menu(self, selection, event):

        author_id = None
        model, treeiter = selection.get_selected()
        if treeiter:
            author_id = model[treeiter][0]

        menu = Gtk.PopoverMenu()
        menu_model = Gio.Menu()
        menu_model.append('Add new category', 'add_new_category')
        menu_model.append('Add exiting author', 'add_existing_author')
        menu_model.append('Edit author', 'edit_author')
        menu_model.append('Remove author', 'remove_author')
        menu.bind_model(menu_model, 'docview')

        group = Gio.SimpleActionGroup()

        action = Gio.SimpleAction.new('add_new_author', None)
        action.connect('activate', self.edit_author)
        group.add_action(action)
        action = Gio.SimpleAction.new('add_existing_author', None)
        action.connect('activate', self.add_existing_author)
        group.add_action(action)
        action = Gio.SimpleAction.new('edit_author')
        action.connect('activate', self.edit_author, author_id)
        group.add_action(action)
        action = Gio.SimpleAction.new('remove_author')
        action.connect('activate', self.remove_author, author_id, treeiter)
        group.add_action(action)

        self.insert_action_group('docview', group)
        menu.set_relative_to(self.authors_view)
        menu.set_position(Gtk.PositionType.BOTTOM)
        menu.show_all()
        menu.popup()
