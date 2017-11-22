# -*- coding: utf-8 -*-

import sys
import os
import models

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('EvinceDocument', '3.0')
gi.require_version('EvinceView', '3.0')

from gi.repository import EvinceDocument, EvinceView
from gi.repository import GLib, Gio, Gtk, Gdk

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dialog import InputDialog, OpenLibraryDialog, EditAuthorDialog
from views import DocumentView, AuthorView, CategoryView

from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument

class LibraryApp(Gtk.Application):
    
    def __init__(self, *args, **kwargs):
        super(LibraryApp, self).__init__(*args, **kwargs)

        self.builder = Gtk.Builder.new_from_file('ui/main.glade')
        self.window = None
        empty_lib = True
        if os.path.exists('./library.db') and os.stat('./library.db').st_size > 0:
            empty_lib = False
        self.engine = create_engine('sqlite:///library.db')
        self.engine.connect()
        if empty_lib:
            models.Base.metadata.create_all(self.engine)
        self.session_maker = sessionmaker()
        self.session_maker.configure(bind=self.engine)
        self.session = self.session_maker()
        self.current_library = None
        self.document_view = DocumentView(self.session)
        self.author_view = AuthorView(self.session)
        self.category_view = CategoryView(self.session)
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY)

        self.document_view.connect('update_document', self.update_document)
        self.document_view.connect('update_author', self.update_author)
        self.document_view.connect('update_category', self.update_category)
        self.author_view.connect('update_author', self.update_author)
        self.category_view.connect('update_category', self.update_category)
        EvinceDocument.init()

    def do_startup(self):
        
        Gtk.Application.do_startup(self)
        
    def do_activate(self):
        
        if self.window is None:
            self.window = self.builder.get_object('library_main_window')
            self.add_window(self.window)
            self.right_frame = self.builder.get_object('right_frame')
            self.right_view = None
            quit = self.builder.get_object('file_quit')
            quit.connect('activate', self.on_quit)
            new_library = self.builder.get_object('file_new')
            new_library.connect('activate', self.new_library)
            open_library = self.builder.get_object('file_open_library')
            open_library.connect('activate', self.open_library)
            file_import_folder = self.builder.get_object('file_import_folder')
            file_import_folder.connect('activate', self.import_folder)
            file_save = self.builder.get_object('file_save')
            file_save.connect('activate', self.save)
            edit_copy = self.builder.get_object('edit_copy')
            edit_copy.connect('activate', self.copy_text)
            edit_paste = self.builder.get_object('edit_paste')
            edit_paste.connect('activate', self.paste_text)
            status_bar = self.builder.get_object('statusbar')
            status_bar.push(1, 'No library currently loaded')
            
            self.docs_tree = self.builder.get_object('docs_tree')
            self.docs_store = self.builder.get_object('docs_store')
            self.authors_tree = self.builder.get_object('authors_tree')
            self.authors_store = self.builder.get_object('authors_store')
            self.category_tree = self.builder.get_object('cat_tree')
            self.category_store = self.builder.get_object('cat_store')

            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn('ID', renderer, text=0)
            self.docs_tree.append_column(column)
            column.set_visible(False)
            column = Gtk.TreeViewColumn('Title', renderer, text=1)
            self.docs_tree.append_column(column)
            column = Gtk.TreeViewColumn('Authors', renderer, text=2)
            self.docs_tree.append_column(column)

            column = Gtk.TreeViewColumn('ID', renderer, text=0)
            self.authors_tree.append_column(column)
            column.set_visible(False)
            column = Gtk.TreeViewColumn('Author', renderer, text=1)
            self.authors_tree.append_column(column)

            column = Gtk.TreeViewColumn('ID', renderer, text=0)
            self.category_tree.append_column(column)
            column.set_visible(False)
            column = Gtk.TreeViewColumn('Category', renderer, text=1)
            self.category_tree.append_column(column)

            self.docs_tree.connect('row-activated', self.show_doc)
            self.authors_tree.connect('row-activated', self.show_author)
            self.category_tree.connect('row-activated', self.show_category)

            self.docs_tree.connect('button-press-event', self.documents_context_menu)
            self.authors_tree.connect('button-press-event', self.authors_context_menu)

        self.window.show_all()

    def new_library(self, widget):
        
        #builder = Gtk.Builder.new_from_file('ui/input_box.glade')
        #dialog = builder.get_object('input_dialog')
        
        dialog = InputDialog(self.window, 'Enter the name of the library:')
        dialog.set_default_size(200, 100)
        
        result = dialog.run()
        library_name = dialog.entry.get_text()
        dialog.destroy()
        if result == Gtk.ResponseType.OK:
            new_library = models.Library(name=library_name)
            self.session.add(new_library)
            self.session.commit()
            self.current_library = new_library
            status_bar = self.builder.get_object('statusbar')
            status_bar.push(1, 'Current library: {}'.format(self.current_library.name))
            
    def open_library(self, widget):
        
        dialog = OpenLibraryDialog(self.session, parent=self.window)
        result = dialog.run()
        print(result)
        if result == Gtk.ResponseType.OK:
            selection = dialog.get_selection()
            if selection:
                self.current_library = self.session.query(models.Library).get(int(selection))
                status_bar = self.builder.get_object('statusbar')
                status_bar.push(1, 'Current library: {}'.format(self.current_library.name))
            
        dialog.destroy()
        self.load_documents()
        self.load_authors()
        self.load_categories()

    def import_folder(self, widget):
        
        print(widget)
        if not self.current_library:
            dialog = Gtk.MessageDialog(self.window, 0, Gtk.MessageType.INFO,
                                       Gtk.ButtonsType.OK,
                                       'Need to have a library loaded before importing!')
            dialog.run()
            dialog.destroy()
            return
        
        
        dialog = Gtk.FileChooserDialog("Please choose a folder to import", self.window,
                                       Gtk.FileChooserAction.SELECT_FOLDER,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        result = dialog.run()
        if result == Gtk.ResponseType.OK:
            library_root = dialog.get_filename()
            dialog.destroy()
            for root, dirs, files in os.walk(library_root):
                for f in files:
                    if f.endswith('.pdf'):
                        self.add_file(root, f)

            self.load_documents()
        else:
            dialog.destroy()

    def save(self, widget):

        self.session.commit()

    def add_file(self, root, filename):

        full_path = os.path.join(root, filename)
        print('Processing', full_path)
        try:
            parser = PDFParser(open(full_path, 'rb'))
            doc = PDFDocument(parser)
            meta = doc.info[0]
            author = str(meta.get('Author', ''))
            title = str(meta.get('Title'))
        except Exception as ex:
            author = None
            title = f.replace('.pdf', '')
        # keywords = str(meta.get('/Keywords')).split(',')

        new_document = models.Document(title=title, path=full_path, library=self.current_library)

        if author is not None and author != '':
            author_names = author.split()
        else:
            author_names = ['', '']
        if len(author_names) == 2:
            new_author = models.Author(first_name=author_names[0], last_name=author_names[-1],
                                       library=self.current_library)
        elif len(author_names) == 3:
            new_author = models.Author(first_name=author_names[0], last_name=author_names[-1],
                                       middle_name=author_names[1],
                                       library=self.current_library)
        else:
            new_author = None
        self.session.add(new_document)
        if new_author:
            self.session.add(new_author)
        self.session.commit()
        if new_author:
            new_document.authors.append(new_author)
            new_author.documents.append(new_document)
        self.session.commit()

        return new_document, new_author
            
    def load_documents(self):
        
        docs = self.session.query(models.Document).filter(
                models.Document.library_id == self.current_library.id)
        self.docs_store.clear()
        
        for doc in docs:
            authors = '; '.join([str(auth) for auth in doc.authors])
            self.docs_store.append([doc.id, doc.title, authors])
        self.window.show_all()

    def load_authors(self):

        authors = self.session.query(models.Author).filter(
            models.Author.library_id == self.current_library.id)
        self.authors_store.clear()

        for author in authors:
            self.authors_store.append([author.id, str(author)])
        self.window.show_all()

    def load_categories(self):

        categories = self.session.query(models.Category).filter(models.Category.library_id == self.current_library.id).filter(
            models.Category.subcategories.any())
        self.category_store.clear()

        def insert_category(parent, category):
            parent_iter = self.category_store.insert(parent, -1, [category.id, category.name])
            for child in category.subcategories:
                insert_category(parent_iter, child)

        for category in categories:
            if category.parent_id is None:
                insert_category(None, category)
    
    def show_doc(self, *args):
        
        selection = self.docs_tree.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter:
            if self.right_view is not None:
                self.right_view.destroy()
                
            doc_id = model[treeiter][0]
            doc = self.session.query(models.Document).get(doc_id)
            for child in self.right_frame.get_children():
                self.right_frame.remove(child)

            self.right_frame.add(self.document_view.main_widget)
            self.document_view.set_document(doc)
            self.document_view.generate_preview(1)
            self.right_frame.show_all()

    def show_author(self, *args):

        selection = self.authors_tree.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter:
            author_id = model[treeiter][0]
            author = self.session.query(models.Author).get(author_id)
            for child in self.right_frame.get_children():
                self.right_frame.remove(child)

            self.right_frame.add(self.author_view.main_widget)
            self.author_view.set_author(author)
            self.right_frame.show_all()

    def show_category(self, *args):

        selection = self.category_tree.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter:
            cat_id = model[treeiter][0]
            cat = self.session.query(models.Category).get(cat_id)
            for child in self.right_frame.get_children():
                self.right_frame.remove(child)

            self.right_frame.add(self.category_view.main_widget)
            self.category_view.set_category(cat)
            self.right_frame.show_all()

    def documents_context_menu(self, widget, event):

        if event.button == 3:

            menu = Gtk.Menu()
            submenu = Gtk.MenuItem('Add new document')
            submenu.connect('activate', self.add_new_document)
            menu.append(submenu)
            submenu = Gtk.MenuItem('Delete document')
            submenu.connect('activate', self.delete_document, widget)
            menu.append(submenu)

            menu.attach_to_widget(self.docs_tree)
            menu.popup(None, None, None, None, event.button, event.time)

            menu.show_all()

    def add_new_document(self, tree):

        if not self.current_library:
            dialog = Gtk.MessageDialog(self.window, 0, Gtk.MessageType.INFO,
                                       Gtk.ButtonsType.OK, 'Need to have a current library before adding documents!')
            dialog.run()
            dialog.destroy()
            return

        dialog = Gtk.FileChooserDialog('Select document', self.window,
                                       Gtk.FileChooserAction.OPEN,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        dialog.set_select_multiple(True)
        result = dialog.run()
        if result == Gtk.ResponseType.OK:
            files = dialog.get_filenames()
            for f in files:
                root, filename = os.path.split(os.path.abspath(f))
                document, author = self.add_file(root, filename)
                self.docs_store.append([document.id, document.title,
                                        '; '.join([str(author) for author in document.authors])])
        dialog.destroy()

    def delete_document(self, menu, tree):

        selection = tree.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter:
            dialog = Gtk.MessageDialog(self.window, 0, Gtk.MessageType.QUESTION,
                                       Gtk.ButtonsType.YES_NO, 'Are you sure you want to delete this document?')
            dialog.format_secondary_text(
                'The document will only be deleted from the database; it will be left unchanged on disk.')
            response = dialog.run()
            if response == Gtk.ResponseType.YES:
                doc_id = model[treeiter][0]
                doc = self.session.query(models.Document).get(doc_id)
                self.session.delete(doc)
                self.session.commit()
                self.docs_store.remove(treeiter)
                for child in self.right_frame.get_children():
                    self.right_frame.remove(child)
            dialog.destroy()

    def update_document(self, event, document_id, insert_new):

        document = self.session.query(models.Document).get(document_id)
        if insert_new:
            self.docs_store.append([document.id, document.title, '; '.join([str(author) for author in document.authors])])
        else:
            for row in self.docs_store:
                if row[0] == document_id:
                    self.docs_store.set_value(row.iter, 1, document.title)
                    self.docs_store.set_value(row.iter, 2, '; '.join([str(author) for author in document.authors]))
                    break

    def authors_context_menu(self, selection, event):

        if event.button == 3:

            menu = Gtk.Menu()
            submenu = Gtk.MenuItem('Add new author')
            submenu.connect('activate', self.add_new_author)
            menu.append(submenu)
            submenu = Gtk.MenuItem('Delete author')
            submenu.connect('activate', self.delete_author, selection)
            menu.append(submenu)

            menu.attach_to_widget(self.authors_tree)
            menu.popup(None, None, None, None, event.button, event.time)

            menu.show_all()

    def add_new_author(self, menu):

        if not self.current_library:
            dialog = Gtk.MessageDialog(self.window, 0, Gtk.MessageType.INFO,
                                       Gtk.ButtonsType.OK, 'Need to have a current library before adding authors!')
            dialog.run()
            dialog.destroy()
            return

        dialog = EditAuthorDialog()
        result = dialog.run()
        if result == Gtk.ResponseType.OK:
            author = dialog.author
            author.library = self.current_library
            self.session.add(author)
            self.session.commit()
            self.authors_store.append([author.id, str(author)])
        dialog.destroy()

    def delete_author(self, menu, tree):

        selection = tree.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter:
            dialog = Gtk.MessageDialog(self.window, 0, Gtk.MessageType.QUESTION,
                                       Gtk.ButtonsType.YES_NO, 'Are you sure you want to delete this author?')
            dialog.format_secondary_text(
                'The author will be deleted from the database but any documents associated with them will not be changed.')
            response = dialog.run()
            if response == Gtk.ResponseType.YES:
                author_id = model[treeiter][0]
                author = self.session.query(models.Author).get(author_id)
                self.session.delete(author)
                self.session.commit()
                self.authors_store.remove(treeiter)
                for child in self.right_frame.get_children():
                    self.right_frame.remove(child)
            dialog.destroy()

    def update_author(self, event, author_id, insert_new):

        print('updating author {}, new = {}'.format(author_id, insert_new))
        author = self.session.query(models.Author).get(author_id)
        if insert_new:
            self.authors_store.append([author.id, str(author)])
        else:
            for row in self.authors_store:
                if row[0] == author_id:
                    self.authors_store.set_value(row.iter, 1, str(author))
                    break

    def category_context_menu(self, selection, event):

        menu = Gtk.Menu()
        submenu = Gtk.MenuItem('Add new top level category')
        submenu.connect('activate', self.add_new_top_category)
        menu.append(submenu)
        submenu = Gtk.MenuItem('Add new subcategory')
        submenu.connect('activate', self.add_new_subcategory, selection)
        menu.append(submenu)
        submenu = Gtk.MenuItem('Delete category')
        submenu.connect('activate', self.delete_category, selection)
        menu.append(submenu)

        menu.attach_to_widget(self.category_tree)
        menu.popup(None, None, None, None, event.button, event.time)

        menu.show_all()

    def add_new_top_category(self, tree):

        dialog = InputDialog(None, 'Enter category name')
        result = dialog.run()
        if result == Gtk.ResponseType.OK:
            category_name = dialog.entry.get_text()
            new_category = models.Category(name=category_name, library=self.current_library)
            self.session.add(new_category)
            self.session.commit()
            self.category_store.insert(None, -1, [new_category.id, new_category.name])
        dialog.destroy()

    def add_new_subcategory(self, tree, selection):

        dialog = InputDialog(None, 'Enter subcategory name')
        result = dialog.run()
        if result == Gtk.ResponseType.OK:
            model, treeiter = selection.get_selected()
            subcat_name = dialog.entry.get_text()
            if treeiter:
                parent_id = model[treeiter][0]
                new_subcat = models.Category(name=subcat_name, parent_id=parent_id, library=self.current_library)
                self.session.add(new_subcat)
                self.session.commit()
                self.category_store.insert(treeiter, -1, [new_subcat.id, new_subcat.name])

        dialog.destroy()

    def update_category(self, event, category_id, parent_id, insert_new):

        print('updating category {}, parent {}, insert_new = {}'.format(category_id, parent_id, insert_new))
        category = self.session.query(models.Category).get(category_id)
        if parent_id > 0:
            parent = self.session.query(models.Category).get(parent_id)
            parent_iter = [row.iter for row in self.category_store if row[0] == parent.id][0]
        else:
            parent = None
            parent_iter = None
        if insert_new:
            self.category_store.insert(parent_iter, -1, [category.id, category.name])
        else:
            for row in self.category_store:
                if row[0] == category.id:
                    self.category_store.set_value(row.iter, 1, category.name)
                    break

    def copy_text(self, widget):

        focus = self.window.get_focus()
        if isinstance(focus, EvinceView.View):
            self.document_view.pdf_view.copy()
        # can potentially copy other things in here like from trees and whatnot

    def paste_text(self, widget):

        text = self.clipboard.wait_for_text()
        focus = self.window.get_focus()
        if isinstance(focus, Gtk.Editable):
            focus.paste_clipboard()
        print(text)

    def on_quit(self, widget):
        
        self.quit()