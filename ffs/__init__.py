
import anki.importing
from ffs.importing import DirectoryImporter

anki.importing.Importers = anki.importing.Importers + ((_("Directory importer (*.dir)"), DirectoryImporter),)
