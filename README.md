# Codex

## What is it?

Codex is an application for managing your PDF files. If you're anything like me, and since you're reading this you're probably at least somewhat like me, you have a large collection of PDF files that you don't know what to do with. Codex is intended to make managing these files easier by attaching metadata to them. Currently, you can specify the authors of the files, assign documents to categories, and rename those files based on a pattern, much like ID3 editors for MP3 files allow you to do.

Codex stores all your metadata in an SQLite database. It leaves files on the disk unchanged, except when you explicitly tell it to rename them. The files themselves are not indexed, so you can't search inside the PDFs, at least not yet.

## So it's like a shittier Papers then?

Short answer: Yes. Much shittier.

Longer answer: The problem with Papers is that it's very opinionated about how everything should be done. It's a full-blown citations manager with lots of bells and whistles, but what it lacked for me was the very basic functionality of renaming files according to a pattern. Although Codex might add citations and other such things in the future, I'm currently using it primarily to organize my PDFs at scale.

Plus, if I'd just bought Papers I'd never have gotten into the exciting world of Gtk GUI programming.

## Requirements

You'll need Gtk3+ along with PyGObject and all of its introspection facilities. You should be able to get all of that via your favorite package manager. Besides that, the two other external dependencies are `sqlalchemy` for the ORM, `alembic` for migrations (coming soon), and `pdfminer` for extracting metadata on import.

This code is only tested with Python 3 on Linux. For all other operating systems, all bets are off. To run, `git clone` and then run `python src/main.py`.

## This sucks/is garbage/doesn't do [insert thing you wish it did]

Tell me about it. No, really, leave an issue. This is a hobby project and a work in progress. I promise nothing.

## Future functionality

Below is a nonexhaustive list of things I'm thinking about adding:

	* Imports from various websites e.g. arXiv and JSTOR
	* Citations/bibliographic generation
	* Publications
	* Author affiliations
	* More configurability i.e. preferences
	* Search
	* PDF indexing
	* Python packaging
	
These may or may not be added in any particular order, as it suits me and I have the time and inclination. Feel free to contribute a PR if you like.
