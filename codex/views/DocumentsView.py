from gi.repository import GLib, Gio, Gtk, Gdk, GObject
from codex.db import models
from codex.db.settings import get_session
from codex.dialogs import (
    EditAuthorDialog, SelectExistingAuthorDialog, SelectExistingCategoryDialog
)

class DocumentsView(Gtk.Paned):

    __gsignals__ = {
        'update_document_global': (GObject.SIGNAL_RUN_FIRST, None, (int, bool)),
        'update_author_global': (GObject.SIGNAL_RUN_FIRST, None, (int, bool)),
        'update_category_global': (GObject.SIGNAL_RUN_FIRST, None, (int, int, bool))
    }

    def __init__(self, *args, **kwargs):

        kwargs['orientation'] = Gtk.Orientation.HORIZONTAL
        super().__init__(**kwargs)

        scrolled_window = Gtk.ScrolledWindow()
        self.documents_tree = Gtk.TreeView()
        scrolled_window.add(self.documents_tree)
        self.detail_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.session = get_session()

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('ID', renderer, text=0)
        self.documents_tree.append_column(column)
        column.set_visible(False)
        column.set_resizable(True)
        column = Gtk.TreeViewColumn('Title', renderer, text=1)
        column.set_sort_column_id(1)
        column.set_resizable(True)
        self.documents_tree.append_column(column)
        column = Gtk.TreeViewColumn('Authors', renderer, text=2)
        column.set_sort_column_id(2)
        column.set_resizable(True)
        self.documents_tree.append_column(column)
        column = Gtk.TreeViewColumn('Categories', renderer, text=3)
        column.set_sort_column_id(3)
        column.set_resizable(True)
        self.documents_tree.append_column(column)
        column = Gtk.TreeViewColumn('Shelf', renderer, text=4)
        column.set_sort_column_id(4)
        column.set_resizable(True)
        self.documents_tree.append_column(column)

        filler = Gtk.Box()
        filler.set_size_request(40, 480)
        self.pack1(scrolled_window, True, True)
        self.pack2(filler, True, False)

        self.documents_tree.set_activate_on_single_click(True)
        self.documents_tree.connect('row-activated', self.on_selected)

    def on_selected(self, view: Gtk.TreeView, path: Gtk.TreePath, column: Gtk.TreeViewColumn):

        selection: Gtk.TreeSelection = view.get_selection()
        if selection:
            model, treeiter = selection.get_selected()
            doc_id = model[treeiter][0]
            document: models.Document = self.session.query(models.Document).get(doc_id)
            self.remove(self.get_child2())
            detail_view = DocumentDetailView(document)
            detail_view.connect('update_author', self._update_author)
            self.pack2(detail_view, False, True)
            self.show_all()

    def _update_author(self, widget, author_id, insert_new):

        self.emit('update_author_global', author_id, insert_new)


class DocumentDetailView(Gtk.Grid):

    __gsignals__ = {
        'update_document': (GObject.SIGNAL_RUN_FIRST, None, (int, bool)),
        'update_author': (GObject.SIGNAL_RUN_FIRST, None, (int, bool)),
        'update_category': (GObject.SIGNAL_RUN_FIRST, None, (int, int, bool))
    }

    def __init__(self, document: models.Document, **kwargs):

        super().__init__(**kwargs)

        self.document = document
        self.set_size_request(320, 480)
        self.session = get_session()

        self.authors_store = Gtk.ListStore(int, str)
        self.categories_store = Gtk.TreeStore(int, str)

        file_label = Gtk.Label(label='Filename')
        title_label = Gtk.Label('Title')
        authors_label = Gtk.Label('Authors')
        categories_label = Gtk.Label('Categories')
        preview_label = Gtk.Label('Preview')
        rename_label = Gtk.Label('Rename pattern')

        labels = [file_label, title_label, authors_label, categories_label, preview_label, rename_label]

        self.file_entry = Gtk.Entry()
        self.title_entry = Gtk.Entry()
        self.authors_view = Gtk.TreeView()
        self.authors_view.set_model(self.authors_store)
        self.categories_view = Gtk.TreeView()
        self.categories_view.set_model(self.categories_store)
        self.preview_scroll = Gtk.ScrolledWindow()
        self.rename_entry = Gtk.Entry()

        views = [self.file_entry, self.title_entry, self.authors_view,
                 self.categories_view, self.preview_scroll, self.rename_entry]

        for i, (label, view) in enumerate(zip(labels, views)):
            label.set_halign(Gtk.Align.END)
            label.set_padding(10, 0)
            view.set_halign(Gtk.Align.START)
            view.set_margin_top(10)
            view.set_margin_bottom(10)
            view.set_size_request(200, 40)
            self.attach(label, 0, i, 1, 1)
            self.attach(view, 1, i, 1, 1)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('ID', renderer, text=0)
        self.authors_view.append_column(column)
        column.set_visible(False)
        column = Gtk.TreeViewColumn('Name', renderer, text=1)
        column.set_resizable(True)
        column.set_sort_column_id(1)
        self.authors_view.append_column(column)

        self.authors_view.connect('button_press_event', self.on_button_press)
        self.categories_view.connect('button_press_event', self.on_button_press)
        self._set_document_data()

    def _set_document_data(self):

        self.file_entry.set_text(self.document.path)
        self.title_entry.set_text(self.document.title)

        session = get_session()

        self.authors_store.clear()
        for author in self.document.authors:
            self.authors_store.append([author.id, str(author)])

        self.categories_store.clear()

        def insert_category(parent, category):
            parent_iter = self.categories_store.insert(parent, -1, [category.id, category.name])
            for child in category.subcategories:
                if child in self.document.categories:
                    insert_category(parent_iter, child)

        for category in self.document.categories:
            if category.parent_id is None:
                insert_category(None, category)

    def on_button_press(self, widget, event):

        print(widget, event)
        if event.button == 3 and widget == self.authors_view:
            self.authors_context_menu(self.authors_view.get_selection(), event)
        elif event.button == 3 and widget == self.categories_view:
            self.categories_context_menu(self.categories_view.get_selection(), event)

    def authors_context_menu(self, selection, event):

        author_id = None
        model, treeiter = selection.get_selected()
        if treeiter:
            author_id = model[treeiter][0]

        menu = Gtk.PopoverMenu()
        menu_model = Gio.Menu()
        menu_model.append('Add new author', 'add_new_author')
        menu_model.append('Add existing author', 'add_existing_author')
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

    def categories_context_menu(self, selection, event):

        category_id = None
        model, treeiter = selection.get_selected()
        if treeiter:
            category_id = model[treeiter][0]

        menu = Gtk.PopoverMenu()
        menu_model = Gio.Menu()
        menu_model.append('Add new category', 'add_new_category')
        menu_model.append('Add existing category', 'add_existing_category')
        menu_model.append('Edit category', 'edit_category')
        menu_model.append('Remove category', 'remove_category')
        menu.bind_model(menu_model, 'docview')

        group = Gio.SimpleActionGroup()

        action = Gio.SimpleAction.new('add_new_category', None)
        action.connect('activate', self.edit_category)
        group.add_action(action)
        action = Gio.SimpleAction.new('add_existing_category')
        action.connect('activate', self.add_existing_category)
        group.add_action(action)
        action = Gio.SimpleAction.new('edit_category')
        action.connect('activate', self.edit_category, category_id)
        group.add_action(action)
        action = Gio.SimpleAction.new('remove_category')
        action.connect('activate', self.remove_category, category_id, treeiter)
        group.add_action(action)

        self.insert_action_group('docview', group)
        menu.set_relative_to(self.categories_view)
        menu.set_position(Gtk.PositionType.BOTTOM)
        menu.show_all()
        menu.popup()

    def edit_author(self, _action, _event, author_id=None):

        session = get_session()
        author = session.query(models.Author).get(author_id) if author_id else None
        insert_new = (author_id is None)
        title = 'Edit author' if author else 'Add new author'
        dialog = EditAuthorDialog(self.get_toplevel(), title, author)
        dialog.run()
        edited_author = dialog.author
        if edited_author:
            edited_author.documents.append(self.document)
            session.add(edited_author)
            session.commit()
            # update locally
            self._update_author(edited_author, insert_new)
            # propagate signal upwards
            self.emit('update_author', edited_author.id, insert_new)

    def _update_author(self, author, insert_new):

        if insert_new:
            self.authors_store.append([author.id, str(author)])
        else:
            for row in self.authors_store:
                if row[0] == author.id:
                    self.authors_store.set_value(row.iter, 1, str(author))
                    break

    def add_existing_author(self, _action, _param, author_id=None):

        session = get_session()
        dialog = SelectExistingAuthorDialog(self.get_toplevel(), 'Select author')
        dialog.run()
        selected_author = dialog.selected_author
        if selected_author:
            self.document.authors.append(selected_author)
            session.add(self.document)
            session.commit()
            self._update_author(selected_author, True)
            self.show()

    def remove_author(self, _action, _param, author_id, treeiter):

        session = get_session()
        author = session.query(models.Author).get(author_id)
        self.document.authors.remove(author)
        session.add(self.document)
        session.commit()
        self.authors_store.remove(treeiter)
        self.show()

    def edit_category(self, action, param, category_id=None):

        pass

    def add_new_category(self, *args):

        print(args)

    def add_existing_category(self, _action, _param):

        categories = self.session.query(models.Category).filter(
            ~models.Category.id.in_([cat.id for cat in self.document.categories])).order_by(models.Category.name)

        dialog = SelectExistingCategoryDialog(self.get_toplevel(), categories)
        dialog.run()

    def remove_category(self, *args):

        print(args)