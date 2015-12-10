# ankideckffs

(WIP)

## Motivation

You may or may not be like me, but I personally could not stand working with the anki GUI to write, manage, and organize anki cards. When it comes to SQL databases, I think of transactions or data that is "set it and forget it," at least from a non-programmatic perspective. If source code needs to query, update, and delete, then by all means, but I don't want to be doing that by hand.

What kinds of datums do I want to be managing manually? Files and directories. I feel more comfortable and less annoyed if I can just throw some text in a file and grep it later, or organize it in a directory hierarchy to make it easy to find. Combined with some flashy bells and whistles, it sounds promising, no?

## Importing

This plugin must be installed through the same channels as all other anki plugins. (TODO: Get the number place it here) Once installed, you'll have an additional import option which you can use to point at a directory. The import will scan the directory for *.card files, and attempt to import them.

The plugin also allows you to define style.css files and macros in a "macros"-named file. Macros are literal text replacements in any of the *.card files in the same directory. Precedence for CSS and macros will always be on the current directory level and then recursive load the parent directories until the initial directory is hit. Any macros defined in a parent that are redefined in a child will be overwritten by the child. The same holds true for CSS files.

A *.card file must be formatted with declarations of the front and back field.

An example card:

    {{front}}
    This is the front of the card.
    {{back}}
    This is the back of the card.
