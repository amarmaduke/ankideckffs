from anki.importing.anki2 import Importer
from anki.utils import splitFields, joinFields
from anki.lang import ngettext
import os

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
# TODO delete notes / cards that don't map to a file
# TODO map file name and directory name to the actual deck name
# TODO models from files?
# TODO macros to use in files?
# TODO some strange shit with field cache stuff
# TODO what does that conf statement before saving the collection do?

class Parser:

    def parse_note_file(self, path, log):
        note = {}
        key = None
        value = ""
        with open(path, 'r') as f:
            for line in f:
                for word in line.split():
                    if word[-1:] == ":": # Assumed Keyword
                        if key:
                            note[key] = unicode(value.strip(), "utf8")
                        key = word[:-1]
                        value = ""
                    else: # Everything else is dumped into the value
                        value = value + " " + word
            note[key] = unicode(value.strip(), "utf8")
        return note

    def parse_notes(self, path, log):
        path = path[0:-4]
        log.append(path + "\n")
        notes = []
        for root, dirs, files in os.walk(path):
            for name in files:
                file_path = os.path.join(root, name)
                note = self.parse_note_file(file_path, log)
                note["Filename"] = name
                log.append(str(note))
                notes.append(note)
        return notes

            # TODO subdirectories
            #for name in dirs:
            #    log.append(os.path.join(root, name) + "\n")

class DirectoryImporter(Importer):

    def run(self):
        parser = Parser()
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


        queue = parser.parse_notes(self.file, self.log)

        # Check for updates
        nids = []
        update = []
        add = []
        for note in col.db.execute("select * from notes"):
            note = list(note)
            match = None
            for n in queue:
                fields = splitFields(note[6])
                if n["Filename"] == fields[0]:
                    if n["Front"] != fields[1]        \
                            or n["Back"] != fields[2]  \
                            or n["Source"] != fields[3]:
                        flds = [n["Filename"], n["Front"], n["Back"], n["Source"]]
                        note[6] = joinFields(flds)
                        update.append(note)
                    match = n
            if match:
                queue.remove(match)
        for note in queue:
            add.append(note)
        if len(update) > 0:
            col.db.executemany(
                "insert or replace into notes values (?,?,?,?,?,?,?,?,?,?,?)",
                update)
            #col.updateFieldCache(update) TODO investigate why this breaks
            #col.tags.registerNotes(update)

        for textfile in add:
            note = col.newNote()
            note["Filename"] = textfile["Filename"]
            note["Front"] = textfile["Front"]
            note["Back"] = textfile["Back"]
            note["Source"] = textfile["Source"]
            p = "\n" + str(note.id) + " " + str(note.guid) + " " + str(note.mid) + " " + str(note.fields) + " " + str(note.data) + "\n";
            self.log.append(p);
            col.addNote(note)
            nids.append(note.id)

        added_cards = []
        for card in col.db.execute("select * from cards"):
            card = list(card)
            if card[1] in nids:
                added_cards.append(card[0])
        cc = len(added_cards) + len(update)
        self.log.append(
            ngettext("%d card imported.", "%d cards imported.", cc) % cc)
        col.decks.setDeck(added_cards, deck)
        #col.conf['nextPos'] = self.dst.db.scalar(
        #    "select max(due)+1 from cards where type = 0") or 0
        col.save()
        col.db.execute("vacuum")
        col.db.execute("analyze")
