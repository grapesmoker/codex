# -*- coding: utf-8 -*-

import sys
import os
import models

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gio, Gtk

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class LibraryApp(Gtk.Application):
    
    def __init__(self, *args, **kwargs):
        super(LibraryApp, self).__init__(*args, **kwargs)
        self.builder = Gtk.Builder.new_from_file('ui/main.glade')
        self.window = None
        empty_lib = True
        if os.path.exists('./library.db'):
            empty_lib = False
        self.engine = create_engine('sqlite:///library.db')
        self.engine.connect()
        if empty_lib:
            models.Base.metadata.create_all(self.engine)
        self.session_maker = sessionmaker()
        self.session_maker.configure(bind=self.engine)
        self.session = self.session_maker()
        self.current_library = None
        
    def do_startup(self):
        
        Gtk.Application.do_startup(self)
        
    def do_activate(self):
        
        if self.window is None:
            self.window = self.builder.get_object('library_main_window')
            self.add_window(self.window)
            quit = self.builder.get_object('file_quit')
            quit.connect('activate', self.on_quit)
            new_library = self.builder.get_object('file_new')
            new_library.connect('activate', self.new_library)
            
        self.window.show_all()
        
    def new_library(self, widget):
        
        print(widget)
        d = Gtk.MessageDialog(self,
                              0, Gtk.MessageType.INFO,
                              Gtk.ButtonsType.OK,
                              'Enter library name')
        entry = Gtk.Entry()
        entry.show()
        d.vbox.pack_end(entry)
        entry.connect('activate', lambda _: d.response(Gtk.ResponseType.OK))

        result = d.run()
        library_name = entry.get_text().decode('utf8')
        d.destroy()
        if result == Gtk.ResponseType.OK:
            new_library = models.Library(name=library_name)
            self.session.add(new_library)
            self.session.commit()
            self.current_library = new_library
    
    def on_quit(self):
        
        self.quit()