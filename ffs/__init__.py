
from anki.importing import Importers
from importing import DirectoryImporter

Importers = Importers + (_("Directory importer (*.dir)"), DirectoryImporter)
