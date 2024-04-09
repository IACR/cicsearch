"""Underlying utility functions for 
1. inserting and updating the database
2. performing a search on the database.

"""

import argparse
from datetime import datetime, timezone
from enum import Enum
import json
import math
import sys
import xapian
#from flask import current_app as app

try:
    from model import Document
except:
    from .model import Document

TITLE_WEIGHT = 5
AUTHOR_WEIGHT = 3

class SearchPrefix(Enum):
    TITLE = 'S'
    AUTHOR = 'A'
    NAME = 'P'
    CREATED = 'D'
    MODIFIED = 'XU'
    CATEGORY = 'XC'
    YEAR = 'Y'
    ID = 'Q'

class SlotNumber(Enum):
    CREATED = 0 # holds 20201207 for Dec 7 2020 for range queries
    LASTMODIFIED = 1 # e.g., 20201221
    AGE_WEIGHT = 2 # scoring feature to favor newer papers.
    SORT_KEY = 3 # sorts by YYYY-mm-dd

def index_document(paper: Document,
                   writable_db,
                   termgenerator=None):
    """Index the paper. It returns no value. It is used by create_index.py.
       args:
          paper: a model.Document
          writable_db: a xapian database. If this is not provided, then
                  app is used to determine the database, open it, and 
                  close it at the end.
          termgenerator: a xapian TermGenerator
    """
    if not termgenerator:
        termgenerator = xapian.TermGenerator()
        termgenerator.set_database(writable_db)
        termgenerator.set_stemmer(xapian.Stem("en"))
        termgenerator.set_flags(termgenerator.FLAG_SPELLING);

    doc = xapian.Document()
    docid = SearchPrefix.ID.value + paper.docid
    doc.add_boolean_term(docid)
    termgenerator.set_document(doc)

    termgenerator.index_text(paper.title, 1, SearchPrefix.TITLE.value)
    termgenerator.index_text(paper.title, TITLE_WEIGHT)
    termgenerator.increase_termpos()
    termgenerator.index_text(paper.abstract)
    if paper.body:
        termgenerator.increase_termpos()
        termgenerator.index_text(paper.body)

    for a in paper.authors:
        termgenerator.increase_termpos()
        termgenerator.index_text(a, 1, SearchPrefix.AUTHOR.value)
        termgenerator.index_text(a, AUTHOR_WEIGHT)

    if paper.keywords:
        for keyword in paper.keywords:
            termgenerator.increase_termpos()
            termgenerator.index_text(keyword)

    termgenerator.increase_termpos()
    year = paper.published[0:4]
    termgenerator.index_text(year)
    termgenerator.index_text(year, 1, SearchPrefix.YEAR.value)
    
    data = paper.model_dump(exclude_unset=True,exclude_none=True)
    # This is a heuristic designed to favor recent papers. I've
    # experimented with different techniques but this one is simple.
    # If you change it, a good rule of thumb is to keep the values
    # below 10 or so; otherwise it will dominate any relevance score.
    years = int(year) - 2024
    # One alternative score that worked OK.
    # age_weight = math.sqrt(years)
    # age_weight = 10 * age_weight / (1 + age_weight)
    age_weight = 5 * (2 + years) / (5 + years)
    data['age_weight'] = age_weight
    # Add values in their slots. These are used for scoring and sorting
    doc.add_value(SlotNumber.AGE_WEIGHT.value, xapian.sortable_serialise(round(age_weight, 3)))
    doc.add_value(SlotNumber.SORT_KEY.value, paper.published)
    doc.set_data(json.dumps(data, indent=2))
    writable_db.replace_document(docid, doc)

def search(db_path, offset=0, limit=100, q=None, source=None):
    """Execute a query on the index.

    Args:
       db_path: path to database
       offset: starting offset for paging of results
       limit: number of items to return
       q: raw query string from the user to be applied to any text field
    Returns: dict with the following:
       error: string if an error occurs (no other fields in this case)
       parsed_query: debug parsed query
       estimated_results: number of total results available
       results: an array of results
    """
    if not q:
        return {'estimated_results': 0,
                'parsed_query': '',
                'spell_corrected_query': '',
                'sort_order': '',
                'results': []}
    db = None
    try:
        # Open the database we're going to search.

        db = xapian.Database(db_path)

        # Set up a QueryParser with a stemmer and suitable prefixes
        queryparser = xapian.QueryParser()
        queryparser.set_database(db)
        queryparser.set_stemmer(xapian.Stem("en"))
        queryparser.set_stemming_strategy(queryparser.STEM_SOME)
        # Allow users to type id:1001022
        queryparser.add_prefix('id', SearchPrefix.ID.value)

        # flags are described here: https://getting-started-with-xapian.readthedocs.io/en/latest/concepts/search/queryparser.html
        # FLAG_BOOLEAN enables boolean operators AND, OR, etc in the query
        # FLAG_LOVEHATE enables + and -
        # FLAG_PHRASE enables enclosing phrases in "
        # FLAG_WILDCARD enables things like * signature scheme to expand the *
        flags = queryparser.FLAG_SPELLING_CORRECTION | queryparser.FLAG_BOOLEAN | queryparser.FLAG_LOVEHATE | queryparser.FLAG_PHRASE | queryparser.FLAG_WILDCARD
        # we build a list of subqueries and combine them later with AND.
        if not q:
            return {'error': 'missing query'}
        query_list = []
        if q:
            terms = q.split()
            terms[-1] = terms[-1] + '*'
            for term in terms:
                query_list.append(queryparser.parse_query(term, flags))
        query = xapian.Query(xapian.Query.OP_AND, query_list)
        # Use an Enquire object on the database to run the query
        enquire = xapian.Enquire(db)
        enquire.set_query(query)
        res = {'parsed_query': str(query)}
        # Use source then relevance score.
        # enquire.set_sort_by_value_then_relevance(SLOT_NUMBER, True)
        enquire.set_sort_by_relevance()
        res['sort_order'] = 'sorted by relevance'
        matches = []
        # Retrieve the matched set of documents.
        mset = enquire.get_mset(offset, limit, 100)
        for match in mset:
            item = {'docid': match.docid,
                    'rank': match.rank,
                    'weight': match.weight,
                    'percent': match.percent}
            fields = json.loads(match.document.get_data().decode())
            for k,v in fields.items():
                item[k] = v
            matches.append(item)
        res['estimated_results'] = mset.get_matches_estimated()
        res['results'] = matches
        spell_corrected = queryparser.get_corrected_query_string()
        if spell_corrected:
            res['spell_corrected_query'] = spell_corrected.decode('utf-8')
        else:
            res['spell_corrected_query'] = ''
        db.close()
        return res
    except Exception as e:
        if db:
            db.close()
        return {'error': 'Error in server:' + str(e)}
                            
            
if __name__ == '__main__':
    arguments = argparse.ArgumentParser()
    arguments.add_argument('--dbpath',
                           default='./xapian.db',
                           help='Path to writable database directory.')
    arguments.add_argument('--q',
                           help='basic query')
    args = arguments.parse_args()
    if not args.q:
        print('--q is required')
        sys.exit(2)
    results = search(args.dbpath, 0, 100, args.q)
    print(json.dumps(results, indent=2))
