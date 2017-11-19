# -*- coding: utf-8 -*-

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('EvinceDocument', '3.0')
gi.require_version('EvinceView', '3.0')

from gi.repository import GLib, Gio, Gtk, GdkPixbuf
from gi.repository import EvinceDocument, EvinceView

import os
import wand
from wand.image import Image

import models as models
from dialog import EditAuthorDialog, ExistingAuthorDialog, InputDialog

class DocumentView(object):
        
    template = 'ui/doc_view.glade'
    
    def __init__(self, session, document=None):
        
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
                insert_category(parent_iter, child)

        for category in self.document.categories:
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

    def add_new_top_category(self, *args):

        dialog = InputDialog(None, 'Enter category name')
        result = dialog.run()
        if result == Gtk.ResponseType.OK:
            category_name = dialog.entry.get_text().decode('utf8')
            new_category = models.Category(name=category_name, library=self.document.library)
            self.session.add(new_category)
            self.session.commit()
            self.session.add(self.document)
            self.document.categories.append(new_category)
            self.session.commit()
            self.category_store.insert(None, -1, [new_category.id, new_category.name])

        dialog.destroy()

    def add_subcategory(self, widget, selection):

        dialog = InputDialog(None, 'Enter subcategory name')
        result = dialog.run()
        if result == Gtk.ResponseType.OK:
            model, treeiter = selection.get_selected()
            subcat_name = dialog.entry.get_text().decode('utf-8')
            if treeiter:
                parent_id = model[treeiter][0]
                new_subcat = models.Category(name=subcat_name, parent_id=parent_id, library=self.document.library)
                self.session.add(new_subcat)
                self.session.add(self.document)
                self.session.commit()
                self.document.categories.append(new_subcat)
                self.session.commit()
                self.category_store.insert(treeiter, -1, [new_subcat.id, new_subcat.name])
        dialog.destroy()

    def delete_category(self, widget, selection):

        pass

    def on_save_clicked(self, *args):
        
        self.session.add(self.document)
        self.document.title = self.title.get_text()
        self.session.commit()

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
        submenu = Gtk.MenuItem('Add new author')
        submenu.connect('activate', self.add_new_author)
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
        
    def destroy(self):

        self.main_widget.destroy()


class AuthorView(object):

    template = 'ui/author_view.glade'

    def __init__(self, session, author=None):

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
            print doc.id, doc.title, location, filename
            self.docs_store.append([doc.id, doc.title, location, filename])

    def set_author(self, author):

        self.author = author
        self.load_data()
