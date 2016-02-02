from anki.utils import tmpdir, namedtmp
from anki.importing.anki2 import Anki2Importer
from anki import Collection

class DirectoryImporter(Anki2Importer):

    def run(self, media=None):
        path = namedtmp("dir_importer.anki2")
        deck = Collection(path)
        f = deck.newNote()
        f['Front'] = u"one"; f['Back'] = u"two"
        n = deck.addNote(f)
        assert n == 1
        deck.close()
        # anki/tests/test_collection.py

        self.file = path
        Anki2Importer.run(self)
