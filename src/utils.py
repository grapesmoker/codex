import os

from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument


def rename(pattern, document):

    format_dict = {}
    authors = document.authors
    categories = document.categories

    if '{last_name}' in pattern and len(authors) > 0:
        format_dict['last_name'] = authors[0].last_name
    if '{first_name}' in pattern and len(authors) > 0:
        format_dict['first_name'] = authors[0].first_name
    if '{author}' in pattern:
        if len(authors) > 0:
            format_dict['author'] = str(authors[0]).strip()
        else:
            format_dict['author'] = ''
    if '{authors_last_names}' in pattern:
        format_dict['authors_last_names'] = ', '.join([auth.last_name for auth in authors])
    if '{authors}' in pattern:
        format_dict['authors'] = '; '.join([str(auth).strip() for auth in authors])
    if '{title}' in pattern:
        format_dict['title'] = document.title
    if '{categories}' in pattern:
        format_dict['categories'] = ', '.join([str(cat).strip() for cat in categories])

    new_file_name = pattern.format(**format_dict)
    location = os.path.split(document.path)[0]
    new_location = os.path.join(location, new_file_name)
    if not new_location.endswith('.pdf') or new_location.endswith('.PDF'):
        new_location += '.pdf'

    return new_location


def read_file_metadata(filename, stop_event):

    parser = PDFParser(open(filename, 'rb'))
    doc = PDFDocument(parser)
    meta = doc.info[0]
    author = str(meta.get('Author', ''))
    title = str(meta.get('Title'))

    return author, title