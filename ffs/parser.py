import os

def split_path(path):
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

def parse_file(path, macros = None):
    text = {}
    key = None
    value = ""
    try:
        with open(path, 'r') as f:
            for line in f:
                for word in line.split():
                    if word[-1:] == ":": # Assumed Keyword
                        if key:
                            text[key] = unicode(value.strip(), "utf8")
                        key = word[:-1]
                        value = ""
                    else: # Everything else is dumped into the value
                        word_update = self.macro_match(word, log)
                        if word_update:
                            value = value + " " + word_update
                        else:
                            value = value + " " + word
            text[key] = unicode(value.strip(), "utf8")
    except Exception as error:
        pass
    return text

    def parse_notes(self, path, log):
        path = path[0:-4]
        path_name = self.split_path(path)[-1]
        # log.append(path + "\n")
        notes = []
        for root, dirs, files in os.walk(path):
            # log.append(root + " " + str(dirs) + " " + str(files))
            macros_file = os.path.join(root, "macros")
            macros = self.parse_file(macros_file)

            for name in files:
                if name == "macros":
                    continue
                file_path = os.path.join(root, name)
                relative_path = self.get_relative_path(file_path, path_name, log)
                note = {}
                note = self.parse_file(file_path, macros, log)
                note["Filename"] = relative_path + "/" + name
                note["Deckname"] = relative_path.replace("/", "::")
                log.append(str(note))
                notes.append(note)
        return notes, path_name

class Tree:
    def __init__(self, name):
        self.macros = {}
        self.options = {}
        self.children = []
        self.parent = None
        self.file_paths = []
        self.files = []
        self.name = name

    def __init__(self, path):
        inital_name = split_path(path)[-1]
        self.name = initial_name

        for name in os.listdir(path):
            next_path = os.path.join(path, name)
            if os.path.isdir(next_path):
                tree = Tree(next_path)
                tree.parent = self
                self.children.append(tree)
            else:
                if name == "macros":
                    self.macros = parse_file(next_path)
                else if name == "options":
                    self.options = parse_file(next_path)
                else:
                    self.file_paths.append(next_path)

        for f in self.file_paths:
            text = parse_file(f, self.macros)
            self.files.append(text)

class Parser:

    def macro_match(self, str, log):
        front = str[:2]
        back = str[-2:]
        result = str[2:-2]
        if front == "{{" and back == "}}":
            return result
        return None

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
        # log.append(path + "\n")
        notes = []
        for root, dirs, files in os.walk(path):
            # log.append(root + " " + str(dirs) + " " + str(files))
            macros_file = os.path.join(root, "macros")
            macros = self.parse_file(macros_file)

            for name in files:
                if name == "macros":
                    continue
                file_path = os.path.join(root, name)
                relative_path = self.get_relative_path(file_path, path_name, log)
                note = {}
                note = self.parse_file(file_path, macros, log)
                note["Filename"] = relative_path + "/" + name
                note["Deckname"] = relative_path.replace("/", "::")
                log.append(str(note))
                notes.append(note)
        return notes, path_name
