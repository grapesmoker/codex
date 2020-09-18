import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from codex.db.settings import get_session
from codex.db import models


class OpenLibraryDialog(Gtk.Dialog):

    class Handler(object):

        def on_dialog_ok_clicked(self, dialog):
            dialog.response(Gtk.ResponseType.OK)

        def on_dialog_cancel_clicked(self, dialog):
            dialog.response(Gtk.ResponseType.CANCEL)

    def __init__(self, parent):

        super().__init__(parent=parent)

        self.set_modal(True)
        self.session = get_session()
        self.add_button("_OK", Gtk.ResponseType.OK)
        self.add_button("_Cancel", Gtk.ResponseType.CANCEL)

        self.connect("response", self.on_response)

        content_area = self.get_content_area()
        self.store = Gtk.ListStore(int, str, int)
        self.view = Gtk.TreeView(model=self.store)
        content_area.add(self.view)
        self.load_data(self.session)

        self.selected_library = None

        self.show_all()

    def on_response(self, dialog, response):

        if response == Gtk.ResponseType.OK:
            selection = self.view.get_selection()
            model, treeiter = selection.get_selected()
            self.selected_library = model[treeiter][0]

        self.destroy()

    def load_data(self, session):

        all_libraries = session.query(models.Library).all()
        for lib in all_libraries:
            doc_count = session.query(models.Document).filter(
                models.Document.library_id == lib.id).count()
            self.store.append([lib.id, lib.name, doc_count])

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Id', renderer, text=0)
        self.view.append_column(column)
        column.set_visible(False)
        column = Gtk.TreeViewColumn('Library name', renderer, text=1)
        self.view.append_column(column)
        column = Gtk.TreeViewColumn('Document count', renderer, text=2)
        self.view.append_column(column)

    # def run(self):
    #
    #     result = self.dialog.run()
    #     return result
    #
    # def get_selection(self):
    #
    #     selection = self.view.get_selection()
    #     model, treeiter = selection.get_selected()
    #     if treeiter:
    #         return model[treeiter][0]
    #     else:
    #         return None
    #
    # def destroy(self):
    #
    #     self.dialog.destroy()
