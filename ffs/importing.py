from anki.importing.anki2 import Importer
from anki.utils import splitFields, joinFields
from anki.lang import ngettext
from parser import Tree

# TODO set a "changed" tag for all notes whose field data changed
# TODO Write documentation on github so people know how to use it
# TODO fieldCache and registerNotes are borked. Probably latex \? Not escaped?
# TODO what does that conf statement before saving the collection do?
# TODO fix error message spacing
# TODO options file

class DirectoryImporter(Importer):

    def handle_models(self, notes, new = False):
        col = self.col
        for note in notes:
            model = note["ffsModel"]
            m = None
            if new:
                m = col.models.new(model["name"])
            else:
                m = col.models.byName(model["name"])
                if not m:
                    raise ValueError("Expected model to exist")
            if "latexPre" in model:
                m["latexPre"] = model["latexPre"]
            if "latexPost" in model:
                m["latexPost"] = model["latexPost"]
            if "css" in model:
                m["css"] = model["css"]

            if "fields" in model:
                fields = ["Filename"]
                fields.extend(model["fields"].split())
                field_map = col.models.fieldMap(m)
                field_names = col.models.fieldNames(m)
                for i in range(len(fields)):
                    if i < len(field_names):
                        name = field_names[i]
                        field = field_map[name][1]
                        col.models.renameField(m, field, fields[i])
                    else:
                        field = col.models.newField(fields[i])
                        col.models.addField(m, field)
                if len(fields) < len(field_names):
                    for i in range(len(fields), len(field_names)):
                        name = field_names[i]
                        field = field_map[name][1]
                        col.models.remField(m, field)

            if "templates" in model:
                ts = model["templates"].split()
                for name in ts:
                    found = False
                    for template in m["tmpls"]:
                        if template["name"] == name:
                            found = True
                            if name+" qfmt" in model:
                                template["qfmt"] = model[name+" qfmt"]
                            if name+" afmt" in model:
                                template["afmt"] = model[name+" afmt"]
                            if name+" bqfmt" in model:
                                template["bqfmt"] = model[name+" bqfmt"]
                            if name+" bafmt" in model:
                                template["bafmt"] = model[name+" bafmt"]
                    if not found:
                        template = col.models.newTemplate(name)
                        if name+" qfmt" in model:
                            template["qfmt"] = model[name+" qfmt"]
                        if name+" afmt" in model:
                            template["afmt"] = model[name+" afmt"]
                        if name+" bqfmt" in model:
                            template["bqfmt"] = model[name+" bqfmt"]
                        if name+" bafmt" in model:
                            template["bafmt"] = model[name+" bafmt"]
                        col.models.addTemplate(m, template)
                col.genCards(col.findNotes("*"))
                for template in m["tmpls"]:
                    if template["name"] not in ts:
                        col.models.remTemplate(m, template)

            note["ffsModel"]["id"] = m["id"]
            if new:
                col.models.add(m)
            # Sanity check our note
            for field in col.models.fieldNames(m):
                if field not in note:
                    raise ValueError("Note missing model field, \
                        in file: {0}".format(note["Filename"]))

    def run(self):

        tree = Tree(self.file[:-4])
        queue = tree.parse()
        deck_name = tree.name

        col = self.col
        # Setup a deck
        deck = col.decks.id(deck_name)
        col.decks.select(deck)

        # Make new models
        new_models = []
        old_models = []
        old_model_ids = []
        for note in queue:
            m = col.models.byName(note["ffsModel"]["name"])
            if not m:
                unique = True
                for n in new_models:
                    if note["ffsModel"]["name"] == n["ffsModel"]["name"]:
                        unique = False
                        break
                if unique:
                    new_models.append(note)
            else:
                unique = True
                for n in old_models:
                    if note["ffsModel"]["name"] == n["ffsModel"]["name"]:
                        unique = False
                        break
                if unique:
                    old_models.append(note)
                note["ffsModel"]["id"] = m["id"]
        self.handle_models(new_models, True)

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
                if col.tags.inList("ffsi:owned", tags):
                    raise ValueError("ffs owned note tampered with.")
                continue
            filename = fields[field_map["Filename"][0]]

            deck_check = filename.split('/')[0]
            if col.tags.inList("ffsi:owned", tags) \
                    and deck_name == deck_check:
                deletable = True
            for n in queue:
                om = col.models.byName(n["ffsModel"]["name"])
                if n["Filename"] == filename:
                    flds = []
                    if "fields" in n["ffsModel"]:
                        flds.append(n["Filename"])
                        for field in n["ffsModel"]["fields"].split():
                            if field not in n:
                                raise ValueError("Note missing model field," +
                                    " in file: {0}".format(n["Filename"]))
                            flds.append(n[field])
                    else:
                        for field in col.models.fieldNames(om):
                            flds.append(n[field])
                    if note[2] != om["id"]:
                        old_model_ids.append(note[2])
                        note[2] = int(om["id"])
                    note[6] = joinFields(flds)
                    update.append(note)
                    match = n

            if match:
                queue.remove(match)
            elif deletable:
                delete.append(note[0])

        self.handle_models(old_models)

        for note in queue:
            add.append(note)

        col.remNotes(delete)
        col.db.executemany(
            "insert or replace into notes values (?,?,?,?,?,?,?,?,?,?,?)",
            update)
        #col.updateFieldCache(update)
        #col.tags.registerNotes(update)

        for textfile in add:
            m = col.models.byName(textfile["ffsModel"]["name"])
            col.models.setCurrent(m)
            note = col.newNote()
            note.addTag("ffsi:owned")
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

        # Cleanup models
        for note in old_models:
            m = col.models.byName(note["ffsModel"]["name"])
            if m:
                nids = col.models.nids(m)
                if len(nids) == 0:
                    col.models.rem(m)
        for i in old_model_ids:
            m = col.models.get(i)
            if m:
                nids = col.models.nids(m)
                if len(nids) == 0:
                    col.models.rem(m)

        #col.conf['nextPos'] = self.dst.db.scalar(
        #    "select max(due)+1 from cards where type = 0") or 0
        col.save()
        col.db.execute("vacuum")
        col.db.execute("analyze")
