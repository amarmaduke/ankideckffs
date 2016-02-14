from anki.importing.anki2 import Importer
from anki.utils import splitFields, joinFields
from anki.lang import ngettext
from parser import Tree


# TODO what does that conf statement before saving the collection do?
# TODO set added and updated tags for easier previewing
# TODO options file
# TODO cleanup unused tags or models

class DirectoryImporter(Importer):

    def run(self):

        tree = Tree(self.file[:-4])
        queue = tree.parse()
        deck_name = tree.name

        col = self.col
        # Setup a deck
        deck = col.decks.id(deck_name)
        col.decks.select(deck)

        # Make models
        for note in queue:
            tmp = note["ffsModel"]
            m = col.models.byName(tmp["name"])
            if m is None:
                m = col.models.new(tmp["name"])
                self.log.append(str(tmp) + '\n')
                if "latexPre" in tmp:
                    m["latexPre"] = tmp["latexPre"]
                if "latexPost" in tmp:
                    m["latexPost"] = tmp["latexPost"]
                if "css" in tmp:
                    m["css"] = tmp["css"]
                if "templates" in tmp:
                    templates = tmp["templates"].split()
                    for name in templates:
                        t = col.models.newTemplate(name)
                        if name+" qfmt" in tmp:
                            t["qfmt"] = tmp[name+" qfmt"]
                        if name+" afmt" in tmp:
                            t["afmt"] = tmp[name+" afmt"]
                        if name+" bqfmt" in tmp:
                            t["bqfmt"] = tmp[name+" bqfmt"]
                        if name+" bafmt" in tmp:
                            t["bafmt"] = tmp[name+" bafmt"]
                        col.models.addTemplate(m, t)
                if "fields" in tmp:
                    fields = tmp["fields"].split()
                    for name in fields:
                        field = col.models.newField(name)
                        col.models.addField(m, field)
                field = col.models.newField("Filename")
                col.models.addField(m, field)
                self.log.append(str(m) + '\n')
                self.log.append("rip\n")
                col.models.add(m)
            # Sanity check our note
            for field in col.models.fieldNames(m):
                if field not in note:
                    raise ValueError("Note missing model field, \
                        in file: {0}".format(note["Filename"]))
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
            m = col.models.get(note[2])
            tags = col.tags.split(note[5])
            field_map = col.models.fieldMap(m)
            fields = splitFields(note[6])
            if "Filename" not in field_map:
                if col.tags.inList("ankideckffs:deletable", tags):
                    raise ValueError("ffs owned note tampered with.")
                continue
            filename = fields[field_map["Filename"][0]]

            deck_check = filename.split('/')[0]
            if col.tags.inList("ankideckffs:deletable", tags) \
                    and deck_name == deck_check:
                deletable = True
            for n in queue:
                om = col.models.byName(n["ffsModel"]["name"])
                if n["Filename"] == filename:
                    if m != om:
                        raise ValueError("ffs owned note tampered with")
                    changed = False
                    for field in field_map:
                        if fields[field[0]] != n[field]:
                            changed = True
                            break
                    if changed:
                        flds = []
                        for field in field_map:
                            flds.append(n[field])
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
            m = col.models.byName(textfile["ffsModel"]["name"])
            col.models.setCurrent(m)
            note = col.newNote()
            note.addTag("ankideckffs:deletable")
            fields = col.models.fieldNames(m)
            for field in fields:
                note[field] = textfile[field]
            col.addNote(note)
            nids.append(note.id)
            nids_decks[note.id] = textfile["ffsDeckname"]

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

        # Set the default model to something standard
        basic = col.models.byName("Basic")
        if basic:
            col.models.setCurrent(basic)

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
