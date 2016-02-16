# ankideckffs

## Motivation

You may or may not be like me, but I personally could not stand working with the anki GUI to write, manage, and organize anki cards.
When it comes to SQL databases, I think of transactions or data that is "set it and forget it," at least from a non-programmatic perspective.
If source code needs to query, update, and delete, then by all means, but I don't want to be doing that by hand.
Of course, Anki gives us a interface to interact with so we're not writing the queries or updates ourselves, but it doesn't really seem, that removed.
Maybe that's just me.

What kinds of datums do I want to be managing manually?
Files and directories.
I feel more comfortable and less annoyed if I can just throw some text in a file and grep it later, or organize it in a directory hierarchy to make it easy to find.
Another nice advantage is version controlling my decks.
Combined with some flashy bells and whistles, it sounds promising, no?

## Importing

This plugin must be installed through the same channels as all other anki plugins. (TODO: Get the number place it here)
Once installed, you'll have an additional import option which you can use to point at a directory.
One quirk to note is that you have to import a _file_ through the standard Anki setup.
To get around this you have to have a file named "(directory name).dir".
You then import this dummy file which directs the plugin to the desired directory.

That directory can contain any number of subdirectories (which will then map to sub decks) and files.
The files can be have any extension you like.
There are however three reserved files with strictly no extension: `model`, `macros`, and `options`.
The `options` file is currently unused but it's still reserved.
The `model` file is used to define a given model.
Note another quirk that you must have a model inside the root directory, but this file can just be empty.
The `macros` file is used to define macro key-value pairs that can be used in any other note file to simplify copying around the same text.
Every other file in the directory is treated as a note file.
These three special files also nest in sub directories, so it's not just the root directory but any directory inside and including the root that can define these special files.

### File Syntax

All files follow the same basic syntax: `[[key]] value ... [[otherkey]] value`.
Whitespace is not significant between keys and the first non-whitespace character between a key and a value.
You can think of this as building a dictionary of keys and values, where the value is all the text you wrote after the key, including whitespace, but then trimmed at the front and end of any excess whitespace.
The strings `[[`, `]]`, `{{`, `}}` are reserved and must be escaped in order to use the literal values, e.g. `\{{`.
You don't escape individual characters of the string, but the string in total.
The double brackets are used for macro expansion.
Assuming you have a macro appropriate defined, then `[[key]] {{macroname}}` will replace `{{macroname}}` with whatever the value for that macro key is.

This syntax is used for all files, including the special files `model`, `macros`, and `options`.
Note that key names are context sensitive, so `Front` is a different key than `front`.

### Models

Models are defined by a `model` file.
A note will check its immediate directory for a `model` file and then all of the parent directories afterwards.
As soon as a `model` file is found it is used as the model for that note.
The `model` file has no required keys but there are only a certain collection of keys it will look for and use.
Of those keys there are two special keys, `[[fields]]` and `[[templates]]`.

Here is a list of all used keys:

* name (required)
* css
* fields (\*)
* latexPre
* latexPost
* templates (\*)
* (template name) qfmt (\*\*)
* (template name) afmt (\*\*)
* (template name) bqfmt (\*\*)
* (template name) bafmt (\*\*)

(\*) This fields are parsed in a special way.
The value is taken as usual, but then the value is split on whitespace, all "words" are then used as a desired field or template name

(\*\*) If a template name is defined in the templates key, then the importer will also look for keys that used that templates name, space, and the literals mentioned above.

(\*\*\*) Note that template names and field names can not have spaces in them.

### Macros

Macros are a simple feature to remove unnecessary rewriting.
The original motivation for them was with citing source material for a particular card.
Consider if you have a definition you'd like to memorize, but the definitions are different depending on the book.
In order disambiguate it would be nice to know the source for context, but that lends to retyping the exact same string over and over, so why not simplify with a macro?

Macro files syntax is the exact same as every other file, the only difference is that keys are now "macro keys" with values being the expanded form of the macro.
If you then use a macro in another file, e.g. `{{macro name}}` then the macro will be expanded to associated value.
Searching for macros is done in the same way that models are found.
First we look inside the present directory, then we move up to the parent, and so on, until we hit the root.
If no macro name exists in the hierarchy we error.
We take the first such macro name available to us.

### Notes

Notes are any other file (I prefer the extensions \*.note or \*.txt) that conforms to the file syntax above.
However, because a note must have a model, it is expected that there is an associated key for every field defined in the associated model.
If this is not true then the importer will error.
This is in contrast to supplying default values for missing fields, the reason error was chosen over defaults is mostly low friction.

Another detail is that the key `Filename` is reserved.
You can not, and should not define this field in your notes.
This field is forced upon any model you define and is used to determine if two notes are the same.
The field holds not just the filename but the relative path from the root directory to its location.

## After Importing

Once you've imported your collection of notes into Anki it is advised that you don't make any changes to the notes inside Anki itself.
Obviously, the entire point of this plugin is for you to make those changes on the file system, so doing it inside Anki would kind of defeat the purpose.

However, every imported card has an `ffsi:owned` tag.
If you wish to take a given note for yourself yet still use the importer for other notes, then remove this tag.
The importer can still find the card and note if it remains in the deck, but will never delete notes that it does not claim to own.
There are two other tags that will be of use as well: `ffsi:added` and `ffsi:changed`.
These tags are set at import-time to brand new notes or notes were either the model or the field data has changed.
These offer a quick way to preview all of the changes you've made and correct mistakes.

## Bugs and Feature Requests

This is still a very young plugin, and to be honest many of the choices were lowest-cost / least-friction decided.
I wanted this plugin for myself, and I wanted it fast, and so here we are.
If you happen to stumble across a bug or a feature that you'd like to be added please make an Issue on github.

Pull requests that fix said problems or add said features are also welcome of course.
