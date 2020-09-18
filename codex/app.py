# -*- coding: utf-8 -*-

import sys
import os
import glob
import threading
import shutil

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('EvinceDocument', '3.0')
gi.require_version('EvinceView', '3.0')

from gi.repository import EvinceDocument, EvinceView
from gi.repository import GLib, Gio, Gtk, Gdk

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from codex.db import models
    #, OpenLibraryDialog, EditAuthorDialog, ProgressDialog, ProgressWindow, BulkRenameDialog
# from views import DocumentView, AuthorView, CategoryView

from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument

from codex.views.MainView import MainWindow
from codex.db.settings import get_engine, get_session
from codex.dialogs.OpenLibraryDialog import OpenLibraryDialog
from codex.dialogs import NewShelfDialog
from codex.views.DocumentsView import DocumentDetailView


class LibraryApp(Gtk.Application):

    def __init__(self, *args, **kwargs):

        super().__init__(**kwargs)

        self.window = MainWindow()
        self.engine = get_engine()
        self.session = get_session()
        models.Base.metadata.create_all(self.engine)

        self.current_library = None

        quit_action = Gio.SimpleAction.new('quit', None)
        quit_action.connect('activate', self.on_quit)
        self.add_action(quit_action)

        about_action = Gio.SimpleAction.new('about', None)
        about_action.connect('activate', self.on_about)
        self.add_action(about_action)

        new_shelf_action = Gio.SimpleAction.new('new_shelf', None)
        new_shelf_action.connect('activate', self.new_shelf)
        self.add_action(new_shelf_action)

        import_dir_action = Gio.SimpleAction.new('import_directory', None)
        import_dir_action.connect('activate', self.import_directory)
        self.add_action(import_dir_action)

        # action = Gio.SimpleAction.new('update_author', None)
        # action.connect('activate', self.update_author)
        # self.add_action(action)

        self.window.documents_view.connect('update_author_global', self.update_author)

        docs_button_action = Gio.SimpleAction.new('show_docs')

        self.set_accels_for_action('app.new_shelf', ['<Control>n'])

        self._setup_stores()
        self._load_data()

    def _setup_stores(self):

        self.docs_store = Gtk.ListStore(int, str, str, str, str)
        self.window.documents_view.documents_tree.set_model(self.docs_store)
        self.authors_store = Gtk.ListStore(int, str, int)
        self.window.authors_view.authors_tree.set_model(self.authors_store)
        self.categories_store = Gtk.TreeStore(int, str)
        self.window.categories_view.categories_tree.set_model(self.categories_store)

    def _load_data(self):

        self.load_authors()
        self.load_categories()
        self.load_documents()

    def new_shelf(self, action, param):

        dialog = NewShelfDialog(self.window, 'New shelf')
        dialog.set_default_size(200, 100)

        dialog.run()
        if dialog.selected_response == Gtk.ResponseType.OK:
            new_shelf = models.Shelf(name=dialog.name, description=dialog.description)
            self.session.add(new_shelf)
            self.session.commit()

    def select_import_files(self):

        filenames = []

        dialog = Gtk.FileChooserDialog("Please choose PDF files to import", self.window,
                                       Gtk.FileChooserAction.OPEN,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        pdf_filter = Gtk.FileFilter()
        pdf_filter.set_name('PDF files')
        pdf_filter.add_mime_type('application/pdf')
        dialog.add_filter(pdf_filter)
        dialog.set_select_multiple(True)

        result = dialog.run()
        if result == Gtk.ResponseType.OK:
            filenames = dialog.get_filenames()
        dialog.destroy()
        return filenames

    def select_import_folder(self):

        library_root = None

        dialog = Gtk.FileChooserDialog("Please choose a folder to import", self.window,
                                       Gtk.FileChooserAction.SELECT_FOLDER,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        result = dialog.run()
        if result == Gtk.ResponseType.OK:
            library_root = dialog.get_filename()
        dialog.destroy()
        return library_root

    def import_directory(self, action, param):

        library_root = self.select_import_folder()
        if library_root:
            pdf_files = glob.glob(library_root + '/**/*.pdf', recursive=True)

            # this is slightly inelegant but it's not worth the bother of
            # the complexity to break this out into a worker thread
            while Gtk.events_pending():
                Gtk.main_iteration()
            num_files = float(len(pdf_files))
            for i, filename in enumerate(pdf_files):
                self.window.status_bar.push(1, 'Loading {}'.format(filename))
                self.window.progress_bar.set_fraction((i + 1) / num_files)
                # again we manually update the main loop to draw the events
                while Gtk.events_pending():
                    Gtk.main_iteration()
                self.add_file(filename)
            self.window.status_bar.push(1, f'Loaded {num_files} documents')
            self.load_documents()

    def import_files(self, widget):

        pdf_files = self.select_import_files()
        if pdf_files:
            while Gtk.events_pending():
                Gtk.main_iteration()
            num_files = float(len(pdf_files))
            for i, filename in enumerate(pdf_files):
                self.window.status_bar.push(1, 'Loading {}'.format(filename))
                self.window.progress_bar.set_fraction((i + 1) / num_files)
                # again we manually update the main loop to draw the events
                while Gtk.events_pending():
                    Gtk.main_iteration()
                self.add_file(filename)
            self.window.status_bar.push(1, f'Loaded {num_files} documents')
            self.load_documents()

    def load_documents(self):

        docs = self.session.query(models.Document).all()
        self.docs_store.clear()

        for doc in docs: # type: models.Document
            authors = '; '.join([str(auth).strip() for auth in doc.authors])
            categories = '; '.join([cat.name.strip() for cat in doc.categories])
            shelf = doc.shelf.name if doc.shelf else ''
            self.docs_store.append([doc.id, doc.title.strip(), authors, categories, shelf])
        self.window.show_all()

    def load_authors(self):

        authors = self.session.query(models.Author).all()
        self.authors_store.clear()
        for author in authors: # type: models.Author
            self.authors_store.append([author.id, str(author), len(author.documents)])
        self.window.show_all()

    def load_categories(self):

        categories = self.session.query(models.Category).filter(
            models.Category.subcategories.any()
        )
        self.categories_store.clear()

        def insert_category(parent, category):
            parent_iter = self.categories_store.insert(parent, -1, [category.id, category.name])
            for child in category.subcategories:
                insert_category(parent_iter, child)

        for category in categories:
            if category.parent_id is None:
                insert_category(None, category)

    def add_file(self, filename):

        title = os.path.split(filename)[1]
        new_document = models.Document(title=title, path=filename)
        self.session.add(new_document)
        self.session.commit()

    def update_author(self, widget, author_id, insert_new):

        print(widget)
        print('updating author', author_id, insert_new)

        author: models.Author = self.session.query(models.Author).get(author_id)
        if insert_new:
            self.authors_store.append([author.id, str(author), len(author.documents)])
            print(f'inserted new author {author}')
        else:
            for row in self.authors_store:
                if row[0] == author_id:
                    self.authors_store.set_value(row.iter, 1, str(author))
                    self.authors_store.set_value(row.iter, 2, len(author.documents))
                    break
            print(f'edited existing author {author}')

    def do_startup(self):

        Gtk.Application.do_startup(self)

    def do_activate(self):

        self.add_window(self.window)
        self.window.show_all()

    def on_quit(self, action, param):

        self.quit()

    def on_about(self, action, param):

        print('some about info goes here')