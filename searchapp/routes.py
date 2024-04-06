"""This implements the REST API for search functionality.
"""
import datetime
from io import BytesIO
import json
from flask import Blueprint, render_template, request, url_for, jsonify
from flask import current_app as app
from .index.search_lib import search, index_document
from .index.model import Document
import xapian

search_bp = Blueprint('search_bp',
                      __name__,
                      template_folder='templates',
                      static_folder='static')

@search_bp.route('/search', methods=['GET'])
def get_results():
    args = request.args.to_dict()
    if 'q' not in args:
        response = jsonify({'error': 'missing queries'})
    else:
        if 'd' in args: # for a test instance.
            db_path = app.config['TEST_XAPIAN_DB_PATH']
        else:
            db_path = app.config['XAPIAN_DB_PATH']
        response = jsonify(search(db_path,
                                  offset=args.get('offset', 0),
                                  q=args.get('q')))
    response.headers.add('Access-Control-Allow-Origin', '*');
    return response

# This has no access control on it, but we assume that we're only listening on localhost.
@search_bp.route('/index', methods=['POST'])
def index_documents():
    args = request.get_json(force=True)
    if not args:
        response = jsonify({'error': 'no papers submitted'})
    elif 'papers' not in args:
        response = jsonify({'error': 'missing papers'})
    else:
        db = None
        try:
            papers = args['papers']
            if 'd' in args: # for a test instance.
                db_path = app.config['TEST_XAPIAN_DB_PATH']
            else:
                db_path = app.config['XAPIAN_DB_PATH']
            db = xapian.WritableDatabase(db_path, xapian.DB_OPEN)
            termgenerator = xapian.TermGenerator()
            termgenerator.set_database(db)
            termgenerator.set_stemmer(xapian.Stem("en"))
            termgenerator.set_flags(termgenerator.FLAG_SPELLING);
            for paper in papers:
                doc = Document(**paper)
                index_document(doc, db, termgenerator)
            response = jsonify({'success': '{} docs indexed'.format(len(papers))})
        except Exception as e:
            response = jsonify({'error': str(e)})
        finally:
            if db:
                db.commit()
                db.close()

    response.headers.add('Access-Control-Allow-Origin', '*');
    return response
