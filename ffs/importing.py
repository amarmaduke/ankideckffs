from anki.utils import tmpdir, namedtmp
from anki.importing.anki2 import Anki2Importer
from anki import Collection

model_css = """\
.card {
 font-family: arial;
 font-size: 20px;
 text-align: center;
 color: black;
 background-color: white;
}

#source {
 font-size: 12px;
 position: relative;
 margin-top: 50px;
 margin-left: 300px;
 color: grey;
}
"""

# TODO updating a deck is a mess

class DirectoryImporter(Anki2Importer):

    def run(self, media=None):
        path = namedtmp("dir_importer.anki2")
        col = Collection(path)
        # Setup a deck
        old_did = col.decks.selected()
        col.decks.rename(col.decks.get(old_did), "MyDeck")
        # Make a new model
        m = col.models.copy(col.models.current())
        fields = {}
        fields["Filename"] = col.models.newField("Filename")
        fields["Source"] = col.models.newField("Source")
        col.models.addField(m, fields["Filename"])
        col.models.addField(m, fields["Source"])
        col.models.setSortIdx(m, m["flds"].index(fields["Filename"]))
        # Set styling and templates for model m
        m["css"] = model_css
        t = col.models.newTemplate("MyTemplate")
        t["qfmt"] = "{{Front}}"
        t["afmt"] = "{{FrontSide}} <hr id=answer> {{Back}} <p id='source'>{{Source}}</p>"
        # Remove old template, set new template
        t_old = m["tmpls"][0]
        col.models.addTemplate(m, t)
        col.models.remTemplate(m, t_old)
        col.models.add(m)
        col.models.setCurrent(m)
        #
        m["id"] = "ourmodel"
        # Test note
        f = col.newNote()
        f["Filename"] = u"test.txt"
        f["Front"] = u"CHANGE Some ALL AGAIN"
        f["Back"] = u"ALL OF Differ HOPEFULLY"
        f["Source"] = u"YET NOTHING  Stuff SHOULD CHANGE IT WILL FUCKING WORK"
        col.addNote(f)
        # Always close the collection
        col.close()

        self.file = path
        Anki2Importer.run(self)

    # Our desired method of handling duplicates is much different
    def _uniquifyNote(self, note):
        # For now we'll just compare the filename field
        # But we will need to check that models match up
        for n in self._notes:
            if note.fields["Filename"] == n.fields["Filename"]:
                return False
        return True
