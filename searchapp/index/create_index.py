"""
This is a convenience command line utility for creating an index and
adding documents to the index in the CiC format. 
"""

import argparse
import datetime
import fnmatch
import json
import os
from pathlib import Path
from pypdf import PdfReader
import sys
from typing import List

import xapian

try:
    from .model import Document
    from .search_lib import index_document
except:
    from model import Document
    from search_lib import index_document

assert sys.version_info >= (3,0)

def convert_cic(data: dict) -> Document:
    """Convenience method to convert a CiC document into the Document format."""
    # if 'body' is in the document, we assume 
    title = data['title']
    if 'subtitle' in data and data['subtitle']:
        title += ' ' + data['subtitle']
    print(data)
    if 'published' in data:
        published = data['published'][:10]
    else:
        published = datetime.datetime.now().strftime('%Y-%m-%d')
    doc = Document(docid = data['paperid'],
                   published = published,
                   title = title,
                   authors = [a['name'] for a in data['authors']],
                   url = data['URL'],
                   keywords = data['keywords'],
                   abstract = data['abstract'])
    return doc

if __name__ == '__main__':
    arguments = argparse.ArgumentParser()
    arguments.add_argument('--verbose',
                           action='store_true',
                           help='Whether to print debug info')
    arguments.add_argument('--input_dir',
                           help='Location of json files for documents to be index.')
    arguments.add_argument('--dbpath',
                           default='xapian.db',
                           help='Path to writable database directory.')
    arguments.add_argument('--include_pdf',
                           action='store_true',
                           help = 'Whether to include pdf text as body. This is really slow.')
    args = arguments.parse_args()
    if os.path.isfile(args.dbpath) or os.path.isdir(args.dbpath):
        print('CANNOT OVERWRITE dbpath')
        sys.exit(2)
    db = xapian.WritableDatabase(args.dbpath, xapian.DB_CREATE_OR_OPEN)
    if not args.input_dir:
        print('no --input_dir specified, so adding no documents.')
        db.commit()
        db.close()
        sys.exit(2)

    # Set up a TermGenerator that we'll use in indexing.
    termgenerator = xapian.TermGenerator()
    termgenerator.set_database(db)
    # use Porter's 2002 stemmer
    termgenerator.set_stemmer(xapian.Stem("english")) 
    termgenerator.set_flags(termgenerator.FLAG_SPELLING);
    count = 0
    for root, dirnames, filenames in os.walk(args.input_dir):
        for fname in fnmatch.filter(filenames, 'meta.json'):
            filename = os.path.join(root, fname)
            json_file = Path(filename)
            data = json.loads(json_file.read_text(encoding='UTF-8'))
            # This converts the cic format to the generic indexed Document.
            # data['publised'] has format YYYY-mm-dd HH:MM:SS
            doc = convert_cic(data)
            if args.verbose:
                print('indexing {}'.format(doc.docid))
            if args.include_pdf:
                body = ''
                pdf_file = json_file.parents[0] / Path('main.pdf')
                if pdf_file.is_file():
                    reader = PdfReader(str(pdf_file))
                    for page in reader.pages:
                        body += '\n' + page.extract_text()
                    doc.body = body
                else:
                    print('missing pdf file ' + str(pdf_file))
                    sys.exit(2)
            index_document(doc, db, termgenerator)
            count += 1
            if count % 5000 == 0:
                print(f'{count} documents')
                db.commit()
    db.commit()
    db.close()
    print(f'Indexed {count} documents')

