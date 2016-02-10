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

# TODO clean up empty child databases
# TODO models from files?
# TODO macros to use in files?
# TODO what does that conf statement before saving the collection do?

class Parser:

    def split_path(self, path):
        folders = []
        while True:
            path, folder = os.path.split(path)
            if folder != "":
                folders.append(folder)
            else:
                if path != "":
                    folders.append(path)
                break
        folders.reverse()
        return folders

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

    def get_relative_path(self, path, from_folder, log):
        folders = self.split_path(path)
        result = from_folder
        insert = False
        for folder in folders[:-1]: #ignore the filename
            if insert:
                result = result + "/" + folder
            if folder == from_folder:
                insert = True
        return result

    def parse_notes(self, path, log):
        path = path[0:-4]
        path_name = self.split_path(path)[-1]
        log.append(path + "\n")
        notes = []
        for root, dirs, files in os.walk(path):
            log.append(root + " " + str(dirs) + " " + str(files))
            for name in files:
                file_path = os.path.join(root, name)
                relative_path = self.get_relative_path(file_path, path_name, log)
                note = self.parse_note_file(file_path, log)
                note["Filename"] = relative_path + "/" + name
                note["Deckname"] = relative_path.replace("/", "::")
                notes.append(note)
        return notes, path_name

            # TODO subdirectories
            #for name in dirs:
            #    log.append(os.path.join(root, name) + "\n")

class DirectoryImporter(Importer):

    def run(self):
        parser = Parser()
        queue, deck_name = parser.parse_notes(self.file, self.log)

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
            note["Front"] = textfile["Front"] or "<empty>"
            note["Back"] = textfile["Back"] or "<empty>"
            note["Source"] = textfile["Source"] or "<empty>"
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
        #col.conf['nextPos'] = self.dst.db.scalar(
        #    "select max(due)+1 from cards where type = 0") or 0
        col.save()
        col.db.execute("vacuum")
        col.db.execute("analyze")
