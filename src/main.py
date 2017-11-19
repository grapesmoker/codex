# -*- coding: utf-8 -*-

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('EvinceDocument', '3.0')
gi.require_version('EvinceView', '3.0')

from gi.repository import Gtk
from gi.repository import EvinceDocument

EvinceDocument.init()

from app import LibraryApp

import sys

if __name__ == '__main__':
    
    app = LibraryApp()
    app.run(sys.argv)