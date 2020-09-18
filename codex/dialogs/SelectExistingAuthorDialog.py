from gi.repository import Gtk
from codex.db.models import Author
from codex.db.settings import get_session


class SelectExistingAuthorDialog(Gtk.Dialog):

    def __init__(self, parent, message, **kwargs):

        Gtk.Dialog.__init__(self, message, parent, 0,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                             Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.set_default_size(320, 240)
        self.connect("response", self.on_response)

        self.authors_store = Gtk.ListStore(int, str)
        self.combo_box = Gtk.ComboBox.new_with_model(self.authors_store)

        renderer_text = Gtk.CellRendererText()
        self.combo_box.pack_start(renderer_text, True)
        self.combo_box.add_attribute(renderer_text, "text", 0)
        renderer_text.set_visible(False)

        renderer_text = Gtk.CellRendererText()
        self.combo_box.pack_start(renderer_text, True)
        self.combo_box.add_attribute(renderer_text, "text", 1)

        box: Gtk.Box = self.get_content_area()
        box.pack_start(self.combo_box, False, False, 0)

        self.selected_author = None
        self._load_data()
        self.show_all()

    def _load_data(self):

        session = get_session()
        authors = session.query(Author).all()
        self.authors_store.clear()

        for author in authors:
            self.authors_store.append([author.id, str(author)])

    def on_response(self, dialog, response):

        if response == Gtk.ResponseType.OK:

            combo_iter = self.combo_box.get_active_iter()
            if combo_iter:
                session = get_session()
                model = self.combo_box.get_model()
                print(model is self.authors_store)
                author_id = model[combo_iter][0]
                self.selected_author = session.query(Author).get(author_id)

        dialog.destroy()