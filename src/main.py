# -*- coding: utf-8 -*-

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from app import LibraryApp

import sys

if __name__ == '__main__':
    
    app = LibraryApp()
    app.run(sys.argv)