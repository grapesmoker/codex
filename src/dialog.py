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
        
        
class OpenLibraryDialog(Gtk.Dialog):
    
    def __init__(self, parent, session):
        
        Gtk.Dialog.__init__(self, 'Select library', parent, 0,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.set_default_size(250, 200)

        self.library_store = Gtk.ListStore(int, str, int)
        self.view = Gtk.TreeView(self.library_store)
        
        box = self.get_content_area()
        box.add(self.view)
        self.load_data(session)
        self.show_all()
        
    def load_data(self, session):
        
        all_libraries = session.query(models.Library).all()
        for lib in all_libraries:
            doc_count = session.query(models.Document).filter(
                    models.Library.id == lib.id).count()
            self.library_store.append([lib.id, lib.name, doc_count])
            print(lib.id, lib.name, doc_count)
            
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Id', renderer, text=0)
        self.view.append_column(column)
        column = Gtk.TreeViewColumn('Library name', renderer, text=1)
        self.view.append_column(column)
        column = Gtk.TreeViewColumn('Document count', renderer, text=2)
        self.view.append_column(column)
        
    def get_selection(self):
        
        selection = self.view.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter:
            return model[treeiter][0]
        else:
            return None