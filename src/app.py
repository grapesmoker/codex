# -*- coding: utf-8 -*-

import sys
import os
import models

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('EvinceDocument', '3.0')
gi.require_version('EvinceView', '3.0')

from gi.repository import EvinceDocument
from gi.repository import GLib, Gio, Gtk

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dialog import InputDialog, OpenLibraryDialog
from views import DocumentView, AuthorView

from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument

class LibraryApp(Gtk.Application):
    
    def __init__(self, *args, **kwargs):
        super(LibraryApp, self).__init__(*args, **kwargs)
        self.builder = Gtk.Builder.new_from_file('ui/main3.glade')
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

        self.window.show_all()
        
    def new_library(self, widget):
        
        #builder = Gtk.Builder.new_from_file('ui/input_box.glade')
        #dialog = builder.get_object('input_dialog')
        
        dialog = InputDialog(self.window, 'Enter the name of the library:')
        dialog.set_default_size(200, 100)
        
        result = dialog.run()
        library_name = dialog.entry.get_text().decode('utf8')
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
                        full_path = os.path.join(root, f)
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
                            new_author = models.Author(first_name=author_names[0], last_name=author_names[-1], library=self.current_library)
                        elif len(author_names) == 3:
                            new_author = models.Author(first_name=author_names[0], last_name=author_names[-1], middle_name=author_names[1],
                                                       library=self.current_library)
                        else:
                            new_author = models.Author(first_name='', last_name='', library=self.current_library)
                        self.session.add(new_document)
                        self.session.add(new_author)
                        self.session.commit()
                        new_document.authors.append(new_author)
                        new_author.documents.append(new_document)
                        #self.session.add(self.current_library)
                        #self.current_library.documents.append(new_document)
                        #self.current_library.authors.append(new_author)
                        self.session.commit()
            self.load_documents()
        else:
            dialog.destroy()
            
    def load_documents(self):
        
        docs = self.session.query(models.Document).filter(
                models.Document.library_id == self.current_library.id)
        self.docs_store.clear()
        
        for doc in docs:
            authors = ';'.join([str(auth) for auth in doc.authors])
            self.docs_store.append([doc.id, doc.title, authors])
        self.window.show_all()

    def load_authors(self):

        authors = self.session.query(models.Author).filter(
            models.Author.library_id == self.current_library.id)
        self.authors_store.clear()

        for author in authors:
            self.authors_store.append([author.id, str(author)])
        self.window.show_all()
    
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

    def on_quit(self):
        
        self.quit()