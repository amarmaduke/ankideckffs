from anki.importing.anki2 import Importer
from anki.utils import splitFields, joinFields
from anki.lang import ngettext
from parser import Tree

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

# TODO models from files?
# TODO what does that conf statement before saving the collection do?
# TODO set added and updated tags for easier previewing
# TODO options file

class DirectoryImporter(Importer):

    def run(self):

        tree = Tree(self.file[:-4])
        queue = tree.parse()
        deck_name = tree.name

        col = self.col
        # Setup a deck
        deck = col.decks.id(deck_name)
        col.decks.select(deck)
        # Make a new model
        m = col.models.byName("MyModel")
        if m is None:
            m = col.models.new("MyModel")
            m["css"] = model_css
            m["did"] = deck
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

        # Check for updates
        nids = []
        nids_decks = {}
        update = []
        add = []
        delete = []
        for note in col.db.execute("select * from notes"):
            note = list(note)
            match = None
            deletable = False
            fields = splitFields(note[6])
            deck_check = fields[0].split('/')[0]
            tags = col.tags.split(note[5])
            if col.tags.inList("ankideckffs:deletable", tags) \
                    and deck_name == deck_check:
                deletable = True
            for n in queue:
                if n["Filename"] == fields[0]:
                    if n["Front"] != fields[1]       \
                            or n["Back"] != fields[2] \
                            or n["Source"] != fields[3]:
                        flds = [n["Filename"],n["Front"], n["Back"], n["Source"]]
                        note[6] = joinFields(flds)
                        update.append(note)
                    match = n
            if match:
                queue.remove(match)
            elif deletable:
                delete.append(note[0])

        for note in queue:
            add.append(note)

        col.remNotes(delete)
        col.db.executemany(
            "insert or replace into notes values (?,?,?,?,?,?,?,?,?,?,?)",
            update)
        col.updateFieldCache(update)
        col.tags.registerNotes(update)

        for textfile in add:
            note = col.newNote()
            note.addTag("ankideckffs:deletable")
            note["Filename"] = textfile["Filename"]
            note["Front"] = textfile["Front"]
            note["Back"] = textfile["Back"]
            note["Source"] = textfile["Source"]
            col.addNote(note)
            nids.append(note.id)
            nids_decks[note.id] = textfile["Deckname"]

        added_cards = []
        for card in col.db.execute("select * from cards"):
            card = list(card)
            if card[1] in nids:
                added_cards.append(card)
        cc = len(added_cards) + len(update)
        cd = len(delete)
        self.log.append(
            ngettext(
                "{0} card changed and {1} deleted.",
                "{0} cards changed and {1} deleted.",
                cc).format(cc, cd))
        # TODO improve this loop
        for card in added_cards:
            deck_name = nids_decks[card[1]]
            deck = col.decks.id(deck_name)
            col.decks.setDeck([card[0]], deck)

        # Cleanup empty decks
        children_decks = col.decks.children(deck)
        for child in children_decks:
            cids = col.decks.cids(child[1], True)
            if len(cids) == 0:
                col.decks.rem(child[1])
        #col.conf['nextPos'] = self.dst.db.scalar(
        #    "select max(due)+1 from cards where type = 0") or 0
        col.save()
        col.db.execute("vacuum")
        col.db.execute("analyze")
