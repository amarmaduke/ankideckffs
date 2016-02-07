from anki.importing.anki2 import Importer
from anki.utils import splitFields, joinFields
from anki.lang import ngettext

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
# TODO some strange shit with field cache stuff
# TODO what does vacuum and analyze do in SQLite?
# TODO what does that conf statement before saving the collection do?
# TODO get something simple up and working for reading from the fs (finally)

class DirectoryImporter(Importer):

    def run(self):
        col = self.col
        # Setup a deck
        deck = col.decks.id("MyDeck")
        col.decks.select(deck)
        # Make a new model
        m = col.models.byName("MyModel")
        if m is None:
            m = col.models.new("MyModel")
            m["did"] = deck
            m["css"] = model_css
            fields = {}
            fields["Filename"] = col.models.newField(_("Filename"))
            fields["Front"] = col.models.newField(_("Front"))
            fields["Back"] = col.models.newField(_("Back"))
            fields["Source"] = col.models.newField(_("Source"))
            col.models.addField(m, fields["Filename"])
            col.models.addField(m, fields["Front"])
            col.models.addField(m, fields["Back"])
            col.models.addField(m, fields["Source"])
            col.models.setSortIdx(m, m["flds"].index(fields["Filename"]))
            # Set styling and templates for model m
            t = col.models.newTemplate("MyTemplate")
            t["did"] = deck
            t["qfmt"] = "{{" + _("Front") + "}}"
            t["afmt"] = "{{FrontSide}} <hr id=answer> {{" + _("Back") + "}} <p id='source'>{{" + _("Source") + "}}</p>"
            # Remove old template, set new template
            col.models.addTemplate(m, t)
            col.models.add(m)
            col.models.setCurrent(m)
        # Test note
        f = col.newNote()
        f["Filename"] = u"test.txt"
        f["Front"] = u"This is an update question"
        f["Back"] = u"This is an update answer"
        f["Source"] = u"This is an update source"
        f2 = col.newNote()
        f2["Filename"] = u"test2.txt"
        f2["Front"] = u"This is an update question"
        f2["Back"] = u"This is an update answer"
        f2["Source"] = u"This is an update source"

        queue = []
        queue.append(f)
        queue.append(f2)
        # Check for updates
        nids = []
        update = []
        add = []
        for note in col.db.execute("select * from notes"):
            note = list(note)
            for n in queue:
                fields = splitFields(note[6])
                if n["Filename"] == fields[0]:
                    flds = [n["Filename"], n["Front"], n["Back"], n["Source"]]
                    note[6] = joinFields(flds)
                    update.append(note)
                    match = n
            queue.remove(match)
        for note in queue:
            add.append(note)
            nids.append(note.id)
        if len(update) > 0:
            col.db.executemany(
                "insert or replace into notes values (?,?,?,?,?,?,?,?,?,?,?)",
                update)
            #col.updateFieldCache(update) TODO investigate why this breaks
            #col.tags.registerNotes(update)

        for note in add:
            col.addNote(note)

        added_cards = []
        for card in col.db.execute("select * from cards"):
            card = list(card)
            if card[1] in nids:
                added_cards.append(card[0])
        cc = len(added_cards)
        self.log.append(
            ngettext("%d card imported.", "%d cards imported.", cc) % cc)
        col.decks.setDeck(added_cards, deck)
        col.conf["nextPos"] = col.db.scalar(
            "select max(due)+1 from cards where type = 0") or 0
        col.save()
        col.db.execute("vacuum")
        col.db.execute("analyze")
