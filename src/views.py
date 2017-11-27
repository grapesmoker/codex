# -*- coding: utf-8 -*-

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('EvinceDocument', '3.0')
gi.require_version('EvinceView', '3.0')

from gi.repository import GLib, Gio, Gtk, GObject, Gdk
from gi.repository import EvinceDocument, EvinceView

import os

import models as models
import utils
from dialog import EditAuthorDialog, ExistingAuthorDialog, InputDialog, ExistingCategoryDialog

class DocumentView(GObject.GObject):
        
    template = 'ui/doc_view.glade'

    __gsignals__ = {
        'update_document': (GObject.SIGNAL_RUN_FIRST, None, (int, bool)),
        'update_author': (GObject.SIGNAL_RUN_FIRST, None, (int, bool)),
        'update_category': (GObject.SIGNAL_RUN_FIRST, None, (int, int, bool))
    }

    def __init__(self, session, document=None):

        GObject.GObject.__init__(self)

        self.document = document
        self.session = session
        self.builder = Gtk.Builder.new_from_file(self.template)
        self.builder.connect_signals(self)
        self.main_widget = self.builder.get_object('grid')
        self.authors_tree = self.builder.get_object('authors')
        self.authors_store = self.builder.get_object('authors_store')
        self.category_store = self.builder.get_object('category_store')
        self.category_tree = self.builder.get_object('categories')
        self.authors_tree.set_model(self.authors_store)
        self.preview = self.builder.get_object('preview')
        self.scale = 1.0
        self.pdf_doc = None
        self.pdf_view = EvinceView.View()
        self.pdf_model = EvinceView.DocumentModel()
        self.preview.add(self.pdf_view)
        self.rename_pattern = self.builder.get_object('rename_pattern')
        self.rename_pattern.set_text('{title} - {authors}.pdf')
        self.authors_tree.connect('button_press_event', self.on_button_press)
        self.category_tree.connect('button_press_event', self.on_button_press)
        self.pdf_view.connect('selection-changed', self.pdf_select)

        rename_button = self.builder.get_object('rename')
        rename_button.connect('clicked', self.rename)

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Id', renderer, text=0)
        self.authors_tree.append_column(column)
        column.set_visible(False)
        column = Gtk.TreeViewColumn('Author', renderer, text=1)
        self.authors_tree.append_column(column)

        column = Gtk.TreeViewColumn('Id', renderer, text=0)
        column.set_visible(False)
        self.category_tree.append_column(column)
        column = Gtk.TreeViewColumn('Category', renderer, text=1)
        self.category_tree.append_column(column)

        if self.document:
            self.load_data()
        
    def load_data(self):
        
        self.title = self.builder.get_object('title')
        self.title.set_text(self.document.title)
        self.path = self.builder.get_object('path')
        self.path.set_text(self.document.path)
        
        authors = self.document.authors
        self.authors_store.clear()
        for author in authors:
            self.authors_store.append([author.id, str(author)])

        self.category_store.clear()

        def insert_category(parent, category):
            parent_iter = self.category_store.insert(parent, -1, [category.id, category.name])
            for child in category.subcategories:
                if child in self.document.categories:
                    insert_category(parent_iter, child)

        for category in self.document.categories:
            if category.parent_id is None:
                insert_category(None, category)

    def set_document(self, document):
        
        self.document = document
        self.load_data()
        
    def add_new_author(self, *args):
        
        dialog = EditAuthorDialog()
        result = dialog.run()
        if result == Gtk.ResponseType.OK:
            author = dialog.author
            self.session.add(author)
            self.session.commit()
            author.library = self.document.library
            self.document.authors.append(author)
            author.documents.append(self.document)
            self.session.add(self.document)
            self.authors_store.append([author.id, str(author)])
            self.session.commit()
            self.emit('update_author', author.id, True)

        dialog.destroy()

    def edit_author(self, widget, selection=None):

        author = None
        new_author = True
        if selection:
            model, treeiter = selection.get_selected()
            if treeiter:
                author_id = model[treeiter][0]
                author = self.session.query(models.Author).get(author_id)
                new_author = False

        dialog = EditAuthorDialog(author)

        result = dialog.run()

        if result == Gtk.ResponseType.OK:
            author = dialog.author
            self.session.add(author)
            self.session.commit()
            if new_author:
                author.library = self.document.library
                self.document.authors.append(author)
                author.documents.append(self.document)
                self.session.add(self.document)
                self.authors_store.append([author.id, str(author)])
                self.emit('update_author', author.id, True)
            else:
                for row in self.authors_store:
                    if row[0] == author.id:
                        row[1] = str(author)
                        break
                self.emit('update_author', author.id, False)
            self.session.commit()

        dialog.destroy()


    def add_existing_author(self, *args):

        if self.document:
            authors = self.session.query(models.Author).filter(models.Author.library == self.document.library).all()
        else:
            authors = []

        dialog = ExistingAuthorDialog(authors)
        result = dialog.run()
        if result == Gtk.ResponseType.OK:
            author = dialog.selected_author
            self.authors_store.append([author.id, str(author)])
            self.session.add(author)
            self.session.add(self.document)
            self.document.authors.append(author)
            # self.session.commit()
            # self.load_data()
        dialog.destroy()

    def delete_author(self, widget, selection):

        model, treeiter = selection.get_selected()
        if treeiter:
            author_id = model[treeiter][0]
            author = self.session.query(models.Author).get(author_id)
            self.session.add(self.document)
            self.document.authors.remove(author)
            self.session.commit()
            self.authors_store.remove(treeiter)

    def add_existing_category(self, *args):

        if self.document:
            categories = self.session.query(models.Category).filter(models.Category.library_id == self.document.library_id).filter(
                ~models.Category.id.in_([cat.id for cat in self.document.categories]))
        else:
            categories = []
        dialog = ExistingCategoryDialog(categories)
        result = dialog.run()
        if result == Gtk.ResponseType.OK:
            category = dialog.selected_category
            ancestors = [category]

            def get_ancestor_chain(category):
                if category.parent_id is not None:
                    parent = self.session.query(models.Category).get(category.parent_id)
                    ancestors.append(parent)
                    get_ancestor_chain(parent)

            get_ancestor_chain(category)
            parent_iter = None
            for ancestor in ancestors[::-1]:
                self.session.add(self.document)
                self.document.categories.append(ancestor)
                parent_iter = self.category_store.insert(parent_iter, -1, [ancestor.id, ancestor.name])
                self.session.commit()
        dialog.destroy()

    def add_new_top_category(self, *args):

        dialog = InputDialog(None, 'Enter category name')
        result = dialog.run()
        if result == Gtk.ResponseType.OK:
            category_name = dialog.entry.get_text()
            new_category = models.Category(name=category_name, library=self.document.library)
            self.session.add(new_category)
            self.session.commit()
            self.session.add(self.document)
            self.document.categories.append(new_category)
            self.session.commit()
            self.category_store.insert(None, -1, [new_category.id, new_category.name])
            self.emit('update_category', new_category.id, -1, True)

        dialog.destroy()

    def add_subcategory(self, widget, selection):

        dialog = InputDialog(None, 'Enter subcategory name')
        result = dialog.run()
        if result == Gtk.ResponseType.OK:
            model, treeiter = selection.get_selected()
            subcat_name = dialog.entry.get_text()
            if treeiter:
                parent_id = model[treeiter][0]
                new_subcat = models.Category(name=subcat_name, parent_id=parent_id, library=self.document.library)
                self.session.add(new_subcat)
                self.session.add(self.document)
                self.session.commit()
                self.document.categories.append(new_subcat)
                self.session.commit()
                self.category_store.insert(treeiter, -1, [new_subcat.id, new_subcat.name])
                self.emit('update_category', new_subcat.id, new_subcat.parent_id, True)
        dialog.destroy()

    def delete_category(self, widget, selection):

        model, treeiter = selection.get_selected()
        if treeiter:
            has_children = model.iter_has_child(treeiter)
            category_id = model[treeiter][0]
            category = self.session.query(models.Category).get(category_id)
            self.session.add(self.document)

            def recursive_remove(category):
                if category in self.document.categories:
                    self.document.categories.remove(category)
                for subcat in category.subcategories:
                    recursive_remove(subcat)

            if has_children:
                dialog = Gtk.MessageDialog(None, 0, Gtk.MessageType.QUESTION,
                                           Gtk.ButtonsType.YES_NO,
                                           'Removing a category with children will remove all of its children as well. Are you sure?')
                result = dialog.run()
                if result == Gtk.ResponseType.YES:
                    recursive_remove(category)
                    self.category_store.remove(treeiter)
                dialog.destroy()

            else:
                self.document.categories.remove(category)
                self.category_store.remove(treeiter)

    def on_save_clicked(self, *args):
        
        self.session.add(self.document)
        self.document.title = self.title.get_text()
        self.session.commit()
        self.emit('update_document', self.document.id, False)

    def generate_preview(self, page):

        if self.pdf_doc is None:
            pdf_doc = EvinceDocument.Document.factory_get_document('file://{}'.format(self.document.path))
            self.pdf_model.set_document(pdf_doc)
            self.pdf_view.set_model(self.pdf_model)
            self.pdf_view.reload()
        else:
            self.pdf_model.get_document().load('file://{}'.format(self.document.path))
            self.pdf_view.reload()

    def on_button_press(self, widget, event):

        if event.button == 3 and widget == self.authors_tree:
            self.authors_context_menu(self.authors_tree.get_selection(), event)
        elif event.button == 3 and widget == self.category_tree:
            self.category_context_menu(self.category_tree.get_selection(), event)

    def on_zoom_in_clicked(self, *args):

        self.pdf_view.zoom_in()
        self.scale = self.pdf_model.get_scale()
        self.pdf_view.reload()

    def on_zoom_out_clicked(self, *args):

        self.pdf_view.zoom_out()
        self.scale = self.pdf_model.get_scale()
        self.pdf_view.reload()

    def authors_context_menu(self, selection, event):

        menu = Gtk.Menu()
        submenu = Gtk.MenuItem('Edit author')
        submenu.connect('activate', self.edit_author, selection)
        menu.append(submenu)
        submenu = Gtk.MenuItem('Add new author')
        submenu.connect('activate', self.edit_author, None)
        menu.append(submenu)
        submenu = Gtk.MenuItem('Add existing author')
        submenu.connect('activate', self.add_existing_author)
        menu.append(submenu)
        submenu = Gtk.MenuItem('Delete author')
        submenu.connect('activate', self.delete_author, selection)
        menu.append(submenu)

        menu.attach_to_widget(self.authors_tree)
        menu.popup(None, None, None, None, event.button, event.time)

        menu.show_all()

    def category_context_menu(self, selection, event):

        menu = Gtk.Menu()
        model, treeiter = selection.get_selected()

        submenu = Gtk.MenuItem('Add existing category')
        submenu.connect('activate', self.add_existing_category)
        menu.append(submenu)
        submenu = Gtk.MenuItem('Add new top level category')
        submenu.connect('activate', self.add_new_top_category)
        menu.append(submenu)
        submenu = Gtk.MenuItem('Add subcategory')
        submenu.connect('activate', self.add_subcategory, selection)
        menu.append(submenu)
        submenu = Gtk.MenuItem('Delete category')
        submenu.connect('activate', self.delete_category, selection)
        menu.append(submenu)

        menu.attach_to_widget(self.category_tree)
        menu.popup(None, None, None, None, event.button, event.time)

        menu.show_all()

    def rename(self, widget):

        pattern = self.rename_pattern.get_text()
        new_location = utils.rename(pattern, self.document)
        dialog = Gtk.MessageDialog(None, 0, Gtk.MessageType.QUESTION,
                                   Gtk.ButtonsType.YES_NO, 'Rename document?')
        dialog.format_secondary_text(
            'The document located at \n{}\n will be renamed to \n{}.'.format(self.document.path, new_location))
        response = dialog.run()
        if response == Gtk.ResponseType.YES:
            if os.path.exists(new_location):
                pass
            else:
                os.rename(self.document.path, new_location)
                self.document.path = new_location
                self.path.set_text(new_location)
        dialog.destroy()

        self.session.commit()

    def pdf_select(self, view):

        pass #view.copy()

    def destroy(self):

        self.main_widget.destroy()


class AuthorView(GObject.GObject):

    template = 'ui/author_view.glade'

    __gsignals__ = {
        'update_author': (GObject.SIGNAL_RUN_FIRST, None, (int, bool))
    }

    def __init__(self, session, author=None):

        GObject.GObject.__init__(self)

        self.author = author
        self.session = session
        self.builder = Gtk.Builder.new_from_file(self.template)
        self.builder.connect_signals(self)
        self.main_widget = self.builder.get_object('grid')
        self.docs_tree = self.builder.get_object('documents')
        self.docs_store = self.builder.get_object('documents_store')

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Id', renderer, text=0)
        self.docs_tree.append_column(column)
        column.set_visible(False)
        column = Gtk.TreeViewColumn('Title', renderer, text=1)
        self.docs_tree.append_column(column)
        column = Gtk.TreeViewColumn('Location', renderer, text=2)
        self.docs_tree.append_column(column)
        column = Gtk.TreeViewColumn('File name', renderer, text=3)
        self.docs_tree.append_column(column)

        if self.author:
            self.load_data()

    def load_data(self):

        self.first_name = self.builder.get_object('author_first_name')
        self.first_name.set_text(self.author.first_name or '')
        self.middle_name = self.builder.get_object('author_middle_name')
        self.middle_name.set_text(self.author.middle_name or '')
        self.last_name = self.builder.get_object('author_last_name')
        self.last_name.set_text(self.author.last_name or '')

        documents = self.author.documents
        self.docs_store.clear()

        for doc in documents:
            location, filename = os.path.split(doc.path)
            self.docs_store.append([doc.id, doc.title, location, filename])

    def set_author(self, author):

        self.author = author
        self.load_data()

    def on_save_clicked(self, *args):

        self.session.add(self.author)
        self.author.first_name = self.first_name.get_text()
        self.author.middle_name = self.middle_name.get_text()
        self.author.last_name = self.last_name.get_text()
        self.emit('update_author', self.author.id, False)
        self.session.commit()


class CategoryView(GObject.GObject):

    template = 'ui/category_view.glade'

    __gsignals__ = {'update_category':  (GObject.SIGNAL_RUN_FIRST, None, (int, bool))}

    def __init__(self, session, category=None):

        GObject.GObject.__init__(self)

        self.category = category
        self.session = session
        self.builder = Gtk.Builder.new_from_file(self.template)
        self.builder.connect_signals(self)
        self.main_widget = self.builder.get_object('grid')
        self.subcat_tree = self.builder.get_object('subcategories')
        self.subcat_store = self.builder.get_object('subcategories_store')
        self.parent = self.builder.get_object('parent')
        self.parent_store = self.builder.get_object('parent_store')

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Id', renderer, text=0)
        self.subcat_tree.append_column(column)
        column.set_visible(False)
        column = Gtk.TreeViewColumn('Subcategory', renderer, text=1)
        self.subcat_tree.append_column(column)

        renderer_text2 = Gtk.CellRendererText()
        self.parent.pack_start(renderer_text2, True)
        self.parent.add_attribute(renderer_text2, "text", 1)

        if self.category:
            self.load_data()

    def load_data(self):

        self.name = self.builder.get_object('name')
        self.name.set_text(self.category.name or '')

        subcategories = self.category.subcategories
        self.subcat_store.clear()
        self.parent_store.clear()

        for cat in subcategories:
            self.subcat_store.append([cat.id, cat.name])

        parents = self.session.query(models.Category).filter(models.Category.library == self.category.library)

        for parent in parents:
            if not self.category.find_item(parent):
                parent_iter = self.parent_store.append([parent.id, parent.name])
                if parent.id == self.category.parent_id:
                    self.parent.set_active_iter(parent_iter)

    def set_category(self, category):

        self.category = category
        self.load_data()

    def on_save_clicked(self, *args):

        self.session.add(self.category)
        self.category.name = self.name.get_text()
        self.session.commit()
        self.emit('update_category', self.category.id, self.category.parent_id, False)