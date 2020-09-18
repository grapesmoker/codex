# -*- coding: utf-8 -*-

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('EvinceDocument', '3.0')
gi.require_version('EvinceView', '3.0')

from gi.repository import GLib, Gio, Gtk, Gdk, GObject

from codex.views import AuthorsView, DocumentsView, CategoriesView


class MainWindow(Gtk.ApplicationWindow):

    def __init__(self):

        super().__init__()
        self.set_default_size(640, 480)

        self.stack = Gtk.Stack()
        self.shelf_view = Gtk.Label(label='shelf view goes here')
        self.authors_view = AuthorsView()
        self.documents_view = DocumentsView()
        self.categories_view = CategoriesView()
        # self.authors_button = Gtk.CheckButton(label='Authors')
        # self.documents_button = Gtk.CheckButton(label='Documents')
        # self.categories_button = Gtk.CheckButton(label='Categories')
        self.stack.add_titled(self.shelf_view, 'shelves', 'Shelves')
        self.stack.add_titled(self.authors_view, 'authors', 'Authors')
        self.stack.add_titled(self.documents_view, 'documents', 'Documents')
        self.stack.add_titled(self.categories_view, 'categories', 'Categories')

        self.header = MainHeader(stack=self.stack)

        # self.header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        # self.content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        # self.sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        # self.detail = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        #
        # self.stack_sidebar = Gtk.StackSidebar()
        # self.stack_sidebar.set_stack(self.stack)
        #
        # self.sidebar.pack_start(self.stack_sidebar, True, True, 0)
        # self.content_box.pack_start(self.sidebar, True, True, 0)
        # self.content_box.pack_start(self.detail, True, True, 0)
        # self.scrolled_sidebar = Gtk.ScrolledWindow()
        # self.sidebar.add(self.scrolled_sidebar)
        #
        self.status_bar = Gtk.Statusbar()
        self.progress_bar = Gtk.ProgressBar()
        # self.header_box.pack_start(self.header, False, True, 0)
        self.main_box.pack_start(self.stack, True, True, 0)
        # self.main_box.pack_start(self.content_box, True, True, 0)
        footer_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        footer_box.pack_start(self.status_bar, True, True, 0)
        footer_box.pack_start(self.progress_bar, False, False, 0)

        self.main_box.pack_start(footer_box, False, True, 0)

        self.add(self.main_box)
        self.set_titlebar(self.header)

        self._set_up_tree_views()

    def test(self, data):

        print(data)

    def _set_up_tree_views(self):

        self.docs_tree = Gtk.TreeView()
        self.category_tree = Gtk.TreeView()

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('ID', renderer, text=0)
        self.docs_tree.append_column(column)
        column.set_visible(False)
        column = Gtk.TreeViewColumn('Title', renderer, text=1)
        column.set_resizable(True)
        column.set_sort_column_id(1)
        self.docs_tree.append_column(column)
        column = Gtk.TreeViewColumn('Authors', renderer, text=2)
        column.set_resizable(True)
        column.set_sort_column_id(2)
        self.docs_tree.append_column(column)
        column = Gtk.TreeViewColumn('Categories', renderer, text=3)
        column.set_resizable(True)
        column.set_sort_column_id(3)
        self.docs_tree.append_column(column)

        column = Gtk.TreeViewColumn('ID', renderer, text=0)
        self.category_tree.append_column(column)
        column.set_visible(False)
        column = Gtk.TreeViewColumn('Category', renderer, text=1)
        column.set_sort_column_id(1)
        self.category_tree.append_column(column)


class MainHeader(Gtk.HeaderBar):

    def __init__(self, **kwargs):

        stack = kwargs.pop('stack')

        super().__init__(**kwargs)

        self.switcher = Gtk.StackSwitcher()
        self.switcher.set_stack(stack)

        self.set_custom_title(self.switcher)
        self.switcher.connect('notify::visible-child', self.test)
        # self.authors_button.connect('toggled', lambda x: print('doing', x))

        self.box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        # self.box.pack_start(self.switcher, True, True, 0)
        # self.box.pack_start(self.stack, True, True, 0)
        self.add(self.box)

        self.box.set_hexpand(True)
        self.box.set_vexpand(False)
        self.box.set_halign(Gtk.Align.CENTER)

        self.search = Gtk.Button()
        search_icon = Gio.ThemedIcon(name='edit-find')
        image = Gtk.Image.new_from_gicon(search_icon, Gtk.IconSize.BUTTON)
        self.search.add(image)
        self.box.pack_start(self.search, False, False, 0)

        self.primary_menu = Gtk.MenuButton()

        menumodel = Gio.Menu()
        lib_submenu = Gio.Menu()

        lib_submenu.append('New shelf', 'app.new_shelf')
        lib_submenu.append('Import directory', 'app.import_directory')
        lib_submenu.append('Import files', 'app.import_files')
        lib_submenu.append('Save', 'app.save')
        lib_submenu_item = Gio.MenuItem.new_section('Library', lib_submenu)

        common_submenu = Gio.Menu()
        common_submenu.append('Preferences', 'app.preferences')
        common_submenu.append('Keyboard shortcuts', 'app.shortcuts')
        common_submenu.append('Help', 'app.help')
        common_submenu.append('About', 'app.about')
        common_submenu.append('Quit', 'app.quit')
        common_submenu_item = Gio.MenuItem.new_section(None, common_submenu)

        menumodel.append_item(lib_submenu_item)
        menumodel.append_item(common_submenu_item)

        self.primary_popover = Gtk.PopoverMenu()
        self.primary_popover.bind_model(menumodel)
        self.primary_popover.set_position(Gtk.PositionType.BOTTOM)
        self.primary_menu.set_popover(self.primary_popover)

        self.box.pack_start(self.primary_menu, False, True, 0)

    def test(self, action, param):

        print(action, param)
