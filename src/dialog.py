# -*- coding: utf-8 -*-

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gio, Gtk, Pango

import models
import os
import utils

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

class ProgressDialog(object):

    template = 'ui/progress_bar_window.glade'

    def __init__(self, parent):

        self.builder = Gtk.Builder.new_from_file(self.template)
        self.builder.connect_signals(self)
        self.progress_bar = self.builder.get_object('progressbar')
        self.progress_text = self.builder.get_object('progress_text')
        self.window = self.builder.get_object('progressbar_window')
        self.window.set_transient_for(parent)

    def on_ok_clicked(self, dialog):
        dialog.response(Gtk.ResponseType.OK)

class ProgressWindow(Gtk.Dialog):

    def __init__(self, parent):
        Gtk.Dialog.__init__(self, 'Loading...', parent, 0,
                            (Gtk.STOCK_OK, Gtk.ResponseType.OK))

        grid = Gtk.Grid()
        self.progress_bar = Gtk.ProgressBar()
        self.progress_text = Gtk.Label()

        grid.attach(self.progress_text, 0, 0, 1, 1)
        grid.attach(self.progress_bar, 1, 0, 1, 1)
        self.add(grid)


        
class OpenLibraryDialog(object):
    
    template = 'ui/open_lib_dialog.glade'
    
    class Handler(object):
        
        def on_dialog_ok_clicked(self, dialog):
            dialog.response(Gtk.ResponseType.OK)

        def on_dialog_cancel_clicked(self, dialog):
            dialog.response(Gtk.ResponseType.CANCEL)

    def __init__(self, session, parent=None):
        
        self.session = session
        self.builder = Gtk.Builder.new_from_file(self.template)
        self.builder.connect_signals(self.Handler())
        self.dialog = self.builder.get_object('open_lib_dialog')
        if parent:
            self.dialog.set_transient_for(parent)
        self.view = self.builder.get_object('library_list')
        self.library_store = self.builder.get_object('library_store')
        self.load_data(self.session)
    
    def load_data(self, session):
        
        all_libraries = session.query(models.Library).all()
        for lib in all_libraries:
            doc_count = session.query(models.Document).filter(
                    models.Document.library_id == lib.id).count()
            self.library_store.append([lib.id, lib.name, doc_count])

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Id', renderer, text=0)
        self.view.append_column(column)
        column.set_visible(False)
        column = Gtk.TreeViewColumn('Library name', renderer, text=1)
        self.view.append_column(column)
        column = Gtk.TreeViewColumn('Document count', renderer, text=2)
        self.view.append_column(column)
        
    def run(self):
        
        result = self.dialog.run()
        return result
    
    def get_selection(self):
        
        selection = self.view.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter:
            return model[treeiter][0]
        else:
            return None
        
    def destroy(self):
        
        self.dialog.destroy()
        
        
class EditAuthorDialog(object):
    
    template = 'ui/edit_author_dialog.glade'
    
    def __init__(self, author=None):
        
        self.builder = Gtk.Builder.new_from_file(self.template)
        self.builder.connect_signals(self)
        self.dialog = self.builder.get_object('edit_author_dialog')
        self.author = author
        
        self.first_name = self.builder.get_object('first_name')
        self.last_name = self.builder.get_object('last_name')
        self.middle_name = self.builder.get_object('middle_name')
        
        if self.author:
            self.first_name.set_text(self.author.first_name)
            self.middle_name.set_text(self.author.middle_name)
            self.last_name.set_text(self.author.last_name)
        else:
            self.author = models.Author()
            
    def run(self):
        
        result = self.dialog.run()
        return result
    
    def on_ok_clicked(self, *args):
        
        self.author.first_name = self.first_name.get_text()
        self.author.middle_name = self.middle_name.get_text()
        self.author.last_name = self.last_name.get_text()
        self.dialog.response(Gtk.ResponseType.OK)
        
    def on_cancel_clicked(self, *args):
        
        self.dialog.response(Gtk.ResponseType.CANCEL)
        
    def destroy(self):
        
        self.dialog.destroy()


class ExistingAuthorDialog(object):

    template = 'ui/existing_author_dialog.glade'

    def __init__(self, authors):

        self.builder = Gtk.Builder.new_from_file(self.template)
        self.builder.connect_signals(self)
        self.dialog = self.builder.get_object('existing_author_dialog')
        self.authors = authors
        self.authors_box = self.builder.get_object('authors')
        self.authors_store = self.builder.get_object('authors_store')
        self.authors_box.set_model(self.authors_store)
        self.selected_author = None
        self.load_data()

    def load_data(self):

        self.authors_store.clear()
        for author in self.authors:
            self.authors_store.append([author.id, str(author)])

        renderer_text1 = Gtk.CellRendererText()
        self.authors_box.pack_start(renderer_text1, True)
        self.authors_box.add_attribute(renderer_text1, "text", 0)
        renderer_text1.set_visible(False)

        renderer_text2 = Gtk.CellRendererText()
        self.authors_box.pack_start(renderer_text2, True)
        self.authors_box.add_attribute(renderer_text2, "text", 1)

    def run(self):

        result = self.dialog.run()
        return result

    def on_ok_clicked(self, *args):

        tree_iter = self.authors_box.get_active_iter()
        if tree_iter:
            model = self.authors_box.get_model()
            auth_id = model[tree_iter][0]
            self.selected_author = [auth for auth in self.authors if auth.id == auth_id][0]
        self.dialog.response(Gtk.ResponseType.OK)

    def on_cancel_clicked(self, *args):

        self.dialog.response(Gtk.ResponseType.CANCEL)

    def destroy(self):

        self.dialog.destroy()


class ExistingCategoryDialog(object):

    template = 'ui/existing_category_dialog.glade'

    def __init__(self, categories=None):
        self.builder = Gtk.Builder.new_from_file(self.template)
        self.builder.connect_signals(self)
        self.dialog = self.builder.get_object('existing_category_dialog')
        self.categories = categories
        self.category_tree = self.builder.get_object('categories')
        self.category_store = self.builder.get_object('category_store')
        self.selected_category = None
        self.load_data()

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
        self.category_tree.append_column(column)
        column.set_visible(False)
        column = Gtk.TreeViewColumn('Category', renderer, text=1)
        self.category_tree.append_column(column)

    def run(self):

        result = self.dialog.run()
        return result

    def on_ok_clicked(self, *args):

        selection = self.category_tree.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter:
            category_id = model[treeiter][0]
            self.selected_category = [cat for cat in self.categories if cat.id == category_id][0]
        self.dialog.response(Gtk.ResponseType.OK)

    def on_cancel_clicked(self, *args):

        self.dialog.response(Gtk.ResponseType.CANCEL)

    def destroy(self):

        self.dialog.destroy()


class BulkRenameDialog(object):

    template = 'ui/bulk_rename_dialog.glade'

    def __init__(self, pattern, documents):

        self.documents = documents
        self.pattern = pattern
        self.builder = Gtk.Builder.new_from_file(self.template)
        self.builder.connect_signals(self)
        self.dialog = self.builder.get_object('bulk_rename_dialog')
        self.rename_tree = self.builder.get_object('rename_tree')
        self.rename_store = self.builder.get_object('rename_store')
        self.selected_files = []
        self.load_data()

    def load_data(self):

        for doc in self.documents:
            root, filename = os.path.split(os.path.abspath(doc.path))
            new_root, new_filename = os.path.split(utils.rename(self.pattern, doc))
            self.rename_store.append([doc.id, root, filename, new_filename, True])

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('ID', renderer, text=0)
        column.set_visible(False)
        self.rename_tree.append_column(column)
        renderer = Gtk.CellRendererText()
        renderer.set_property('ellipsize', Pango.EllipsizeMode.END)
        column = Gtk.TreeViewColumn('Directory', renderer, text=1)
        self.rename_tree.append_column(column)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Old filename', renderer, text=2)
        self.rename_tree.append_column(column)
        renderer = Gtk.CellRendererText()
        renderer.set_property('editable', True)
        renderer.connect('edited', self.on_cell_text_edited)
        column = Gtk.TreeViewColumn('New filename', renderer, text=3)
        self.rename_tree.append_column(column)
        renderer = Gtk.CellRendererToggle()
        renderer.connect('toggled', self.on_cell_toggled)
        column = Gtk.TreeViewColumn('Selected', renderer, active=4)
        self.rename_tree.append_column(column)

    def on_cell_toggled(self, widget, path):

        self.rename_store[path][4] = not self.rename_store[path][4]

    def on_cell_text_edited(self, widget, position, edit):

        self.rename_store[position][2] = edit

    def on_ok_clicked(self, *args):

        self.selected_files = [row[0:4] for row in self.rename_store if row[4] is True]
        self.dialog.response(Gtk.ResponseType.OK)

    def on_cancel_clicked(self, *args):

        self.dialog.response(Gtk.ResponseType.CANCEL)

    def on_select_all_clicked(self, *args):

        for row in self.rename_store:
            row[4] = True

    def on_select_none_clicked(self, *args):

        for row in self.rename_store:
            row[4] = False

    def run(self):

        result = self.dialog.run()
        return result

    def destroy(self):

        self.dialog.destroy()