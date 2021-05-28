from gi.repository import GLib, Gio, Gtk, Gdk, GObject
from codex.dialogs.EditCategoryDialog import EditCategoryDialog
from codex.db.settings import get_session
from codex.db import models


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
        self.categories_tree.connect('button_press_event', self.on_button_press)

        self.pack1(scrolled_window)

    def on_button_press(self, widget, event):

        if event.button == 3:
            self.categories_context_menu(self.categories_tree.get_selection(), event)

    def categories_context_menu(self, selection, event):

        category_id = None
        model, treeiter = selection.get_selected()
        if treeiter:
            category_id = model[treeiter][0]
            click_location = self.categories_tree.get_cell_area(treeiter)
        else:
            click_location = Gdk.Rectangle()
            click_location.x = event.x
            click_location.y = event.y
            click_location.height = 1
            click_location.width = 1

        menu = Gtk.PopoverMenu()
        menu_model = Gio.Menu()
        menu_model.append('Add new category', 'add_new_category')
        menu_model.append('Edit category', 'edit_category')
        menu_model.append('Remove category', 'remove_category')
        menu.bind_model(menu_model, 'catview')

        group = Gio.SimpleActionGroup()

        action = Gio.SimpleAction.new('add_new_category')
        action.connect('activate', self.edit_category)
        group.add_action(action)
        action = Gio.SimpleAction.new('edit_category')
        action.connect('activate', self.edit_category, category_id)
        group.add_action(action)
        action = Gio.SimpleAction.new('remove_category')
        action.connect('activate', self.remove_category, category_id, treeiter)
        group.add_action(action)

        self.insert_action_group('catview', group)
        menu.set_relative_to(self.categories_tree)
        menu.set_position(Gtk.PositionType.BOTTOM)
        menu.set_pointing_to(click_location)
        menu.show_all()
        menu.popup()

    def edit_category(self, _action, _event, category_id=None):

        session = get_session()
        category = session.query(models.Category).get(category_id) if category_id else None
        insert_new = (category_id is None)
        title = 'Edit category' if category else 'Add new category'
        dialog = EditCategoryDialog(self.get_toplevel(), title, category)
        dialog.run()
        edited_category = dialog.category
        if edited_category:
            session.add(edited_category)
            session.commit()
            # update locally
            self._update_author(edited_author, insert_new)
            # propagate signal upwards
            self.emit('update_author', edited_author.id, insert_new)

    def remove_category(self, *args):

        print('remove_category', args)
