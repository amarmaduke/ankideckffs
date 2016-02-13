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

def lex_file(path):
    stream = []
    try:
        text = ""
        with open(path, 'r') as f:
            for line in f:
                for char in line:
                    if text.strip() == "[[": # key start
                        stream.append("[[")
                        text = ""
                    elif text[-2:] == "]]": # key end
                        stream.append(text[:-2])
                        stream.append("]]")
                        text = ""
                    elif text.strip() == "{{": # left macro expansion
                        stream.append("{{")
                        text = ""
                    elif text[-2:] == "}}": # right macro expansion
                        stream.append(text[:-2])
                        stream.append("}}")
                        text = ""
                    text = text + char
    except Exception as error:
        pass
    return stream

class Tree:
    def __init__(self, path):
        inital_name = split_path(path)[-1]
        self.macros = {}
        self.options = {}
        self.children = []
        self.parent = None
        self.file_paths = []
        self.files = []
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

    def get_full_name(self):
        result = []
        full_name = ""
        tree = self
        while tree.parent:
            result.append(tree.name)
            tree = tree.parent
        for name in reversed(result)
            full_name = name + "/"
        return full_name

    def expand_macro(self, name):
        result = None
        tree = self
        while (tree.parent and not result)
            if name in tree.macros:
                result = tree.macros[name]
            tree = tree.parent
        return result

    def parse_file(self, path):
        stream = lex_file(path)
        estream = []
        ignore = []
        text = {}

        for i in range(len(stream)):
            if stream[i] == "{{":
                if stream[i + 1] == "{{":
                    raise Error("Can't have nested macros")
                elif stream[i + 1] == "}}":
                    raise Error("Macro name must be nonempty")
                if stream[i + 2] != "}}":
                    raise Error("Expected closing }}")
                value = expand_macro(stream[i + 1].strip())
                if value:
                    estream.append(value)
                    ignore.append(i + 1)
                else:
                    raise Error("Macro name does not exist")
            elif stream[i] != "}}" and i not in ignore:
                estream.append(stream[i])

        for i in range(len(stream)):
            if stream[i] == "[[":
                if stream[i + 1] == "[[":
                    raise Error("Can't have nested key declarations")
                elif stream[i + 1] == "]]":
                    raise Error("Key name must be nonempty")
                if stream[i + 2] != "]]":
                    raise Error("Expected closing ]]")
                if stream[i + 3] == "[[" or stream[i + 3] == "]]":
                    raise Error("Expected field value after key declaration")
                text[stream[i + 1].strip()] = \
                    unicode(stream[i + 3].strip(), "utf8")
        return text

    def parse(self):
        for path in self.file_paths:
            f = self.parse_file(path)
            full_name = self.get_full_name()
            f["Filename"] = full_name + split_path(path)[-1]
            f["Deckname"] = full_name.replace("/", "::")[:-2]
            self.files.append(f)
        for child in self.children:
            f = child.parse()
            self.files.append(f)
        return self.files
