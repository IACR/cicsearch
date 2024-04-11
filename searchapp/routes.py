"""This implements the REST API for search functionality.
"""
import datetime
from io import BytesIO
import json
import functools
import logging

from flask import Blueprint, request, jsonify, abort
from flask import current_app as app
import xapian

from .index.search_lib import search, index_document
from .index.model import Document

search_bp = Blueprint('search_bp',
                      __name__,
                      template_folder='templates',
                      static_folder='static')

def auth_required(f):
    """A simple decorator to check for a valid x-access-token header."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        logging.critical('remote addr is {}'.format(request.remote_addr))
        if app.config['TESTING']:
            app.logger.info('no auth required for testing')
            return f(*args, **kwargs)
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
            if token in app.config['AUTH_TOKENS']:
                return f(*args, **kwargs)
            else:
                app.logger.critical('invalid auth token')
                return abort(403)
        else:
            app.logger.critical('no auth token')
            return abort(403)
    return decorated_function

def _get_dbpath(args):
    """Construct the database path from the arguments."""
    if 'd' in args: # database name
        dbname = args.get('c')
        if dbname in app.config['XAPIAN_PATHS']:
            return app.config['XAPIAN_PATHS'][dbname]
    return app.config['XAPIAN_PATHS']['default']
    

@search_bp.route('/search', methods=['GET'])
def get_results():
    """Search requests are not authenticated."""
    args = request.args.to_dict()
    if 'q' not in args:
        response = jsonify({'error': 'missing queries'})
    db_path = _get_dbpath(args)
    response = jsonify(search(db_path,
                                  offset=args.get('offset', 0),
                                  q=args.get('q')))
    response.headers.add('Access-Control-Allow-Origin', '*');
    return response

@search_bp.route('/index', methods=['POST'])
@auth_required
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
            db_path = _get_dbpath(args)
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
