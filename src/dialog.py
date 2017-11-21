# -*- coding: utf-8 -*-

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gio, Gtk

import models

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
        
        
class OpenLibraryDialog(object):
    
    template = 'ui/open_lib_dialog.glade'
    
    class Handler(object):
        
        def on_dialog_ok_clicked(self, dialog):
            print('clicked ok', dialog)
            dialog.response(Gtk.ResponseType.OK)
        def on_dialog_cancel_clicked(self, dialog):
            print('clicked cancel', dialog)
            dialog.response(Gtk.ResponseType.CANCEL)
            #return Gtk.ResponseType.CANCEL
    
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
            print(lib.id, lib.name, doc_count)
            
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
            print(str(author))
            self.authors_store.append([author.id, str(author)])

        renderer_text1 = Gtk.CellRendererText()
        self.authors_box.pack_start(renderer_text1, True)
        self.authors_box.add_attribute(renderer_text1, "text", 0)

        renderer_text2 = Gtk.CellRendererText()
        self.authors_box.pack_start(renderer_text2, True)
        self.authors_box.add_attribute(renderer_text2, "text", 1)

    def run(self):

        result = self.dialog.run()
        return result

    def on_ok_clicked(self, *args):

        print('ok clicked')
        tree_iter = self.authors_box.get_active_iter()
        if tree_iter:
            model = self.authors_box.get_model()
            auth_id = model[tree_iter][0]
            self.selected_author = [auth for auth in self.authors if auth.id == auth_id][0]
        self.dialog.response(Gtk.ResponseType.OK)

    def on_cancel_clicked(self, *args):

        print('cancel clicked')
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
            print([cat.id for cat in self.categories])
            print(category_id)
            self.selected_category = [cat for cat in self.categories if cat.id == category_id][0]
        self.dialog.response(Gtk.ResponseType.OK)

    def on_cancel_clicked(self, *args):

        self.dialog.response(Gtk.ResponseType.CANCEL)

    def destroy(self):

        self.dialog.destroy()