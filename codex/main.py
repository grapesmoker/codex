# -*- coding: utf-8 -*-

import os
from pathlib import Path
import sys
sys.path.append(str(Path(os.path.curdir).resolve()))

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('EvinceDocument', '3.0')
gi.require_version('EvinceView', '3.0')

from gi.repository import Gtk
from gi.repository import EvinceDocument

EvinceDocument.init()

from codex.app import LibraryApp


if __name__ == '__main__':
    app = LibraryApp()
    app.run(sys.argv)