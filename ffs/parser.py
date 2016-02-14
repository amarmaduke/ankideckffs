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
                    if text[-2:] == "[[": # key start
                        stream.append(text[:-2])
                        stream.append("[[")
                        text = ""
                    elif text[-2:] == "]]": # key end
                        stream.append(text[:-2])
                        stream.append("]]")
                        text = ""
                    elif text[-2:] == "{{": # left macro expansion
                        stream.append(text[:-2])
                        stream.append("{{")
                        text = ""
                    elif text[-2:] == "}}": # right macro expansion
                        stream.append(text[:-2])
                        stream.append("}}")
                        text = ""
                    text = text + char
        stream.append(text)
    except Exception as error:
        pass
    return stream

class Tree:
    def __init__(self, path):
        initial_name = split_path(path)[-1]
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
                    self.macros = self.parse_file(next_path)
                elif name == "options":
                    self.options = self.parse_file(next_path)
                else:
                    self.file_paths.append(next_path)

    def get_full_name(self):
        result = []
        full_name = ""
        prefix_name = ""
        tree = self
        while tree.parent:
            result.append(tree.name)
            tree = tree.parent
        result.append(tree.name)
        for name in reversed(result):
            full_name = full_name + name + "::"
        for name in reversed(result[:-1]):
            prefix_name = prefix_name + name + "/"

        return full_name[:-2], prefix_name

    def expand_macro(self, name):
        tree = self
        while tree.parent:
            if name in tree.macros:
                return tree.macros[name]
            tree = tree.parent
        if name in tree.macros:
            return tree.macros[name]
        return None

    def fix_expanded_stream(self, stream):
        result = []
        text = ""
        for token in stream:
            if token == "[[":
                result.append(text)
                text = ""
                result.append("[[")
            elif token == "]]":
                result.append(text)
                text = ""
                result.append("]]")
            else:
                text = text + token
        result.append(text)
        return result

    def parse_file(self, path):
        stream = lex_file(path)
        if len(stream) == 0:
            raise ValueError("Lexer error, are you doing \
                `[[key]] value {\{macro\}} value` ? file: {0}".format(path))
        estream = []
        ignore = []
        text = {}

        for i in range(len(stream)):
            if stream[i] == "{{":
                if i + 1 >= len(stream):
                    raise ValueError( \
                        "Expected macro name after {{, file: {0}".format(path))
                elif stream[i + 1] == "{{":
                    raise ValueError( \
                        "Can't have nested macros, file: {0}".format(path))
                elif stream[i + 1] == "}}":
                    raise ValueError( \
                        "Macro name must be nonempty, file: {0}".format(path))
                if i + 2 >= len(stream) or stream[i + 2] != "}}":
                    raise ValueError( \
                        "Expected closing }}, file: {0}".format(path))
                value = self.expand_macro(stream[i + 1].strip())
                if value:
                    estream.append(value)
                    ignore.append(i + 1)
                else:
                    raise ValueError( \
                        "Macro name does not exist, file: {0}".format(path))
            elif stream[i] != "}}" and i not in ignore:
                estream.append(stream[i])
        estream = self.fix_expanded_stream(estream)

        for i in range(len(estream)):
            if estream[i] == "[[":
                if i + 1 >= len(estream):
                    raise ValueError( \
                        "Expected key name after [[, file: {0}".format(path))
                elif estream[i + 1] == "[[":
                    raise ValueError( \
                        "Can't have nested key declarations, \
                         file: {0}".format(path))
                elif estream[i + 1] == "]]":
                    raise ValueError( \
                        "Key name must be nonempty, file: {0}".format(path))
                if i + 2 >= len(estream) or estream[i + 2] != "]]":
                    raise ValueError( \
                        "Expected closing ]], file: {0}".format(path))
                if i + 3 >= len(estream) or \
                    estream[i + 3] == "[[" or estream[i + 3] == "]]":
                    raise ValueError(
                        "Expected field value after key declaration, \
                        file: {0}".format(path))
                text[estream[i + 1].strip()] = \
                    estream[i + 3].strip().encode("utf8")
        if not text:
            raise ValueError("Unexpected parser error, file: {0}".format(path))
        return text

    def parse(self):
        for path in self.file_paths:
            f = self.parse_file(path)
            full_name, prefix_name = self.get_full_name()
            f["Filename"] = prefix_name + split_path(path)[-1]
            f["Deckname"] = full_name
            self.files.append(f)
        for child in self.children:
            f = child.parse()
            self.files.extend(f)
        return self.files
