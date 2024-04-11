# A dirt simple fast search engine

This repository contains code for simple search functionality. This
app uses the [xapian library](https://xapian.org/). It is bundled
as a separate app so that the GPL license of xapian does not
contaminate other projects. The code in this library should not be
linked in other projects unless you are prepared to deal with GPL.

This server allows documents to be indexed and searched using only
AJAX calls. It was originally created for cic.iacr.org, but it may be
extended in the future.

## Document schema

The documents that are indexed are modeled by the `model.Document`
class that is written in the [pydantic
2.0](https://docs.pydantic.dev/latest/) API. This code should not be
linked in other projects, but the json schema is quite simple so you
don't really need it in clients:

```
{
  "description": "The model of a document to be indexed.",
  "properties": {
    "docid": {
      "title": "Globally unique document ID",
      "type": "string"
    },
    "published": {
      "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$",
      "title": "Date of publication",
      "type": "string"
    },
    "title": {
      "minLength": 2,
      "title": "The title of the document",
      "type": "string"
    },
    "authors": {
      "items": {
        "type": "string"
      },
      "title": "List of author names",
      "type": "array"
    },
    "url": {
      "title": "URL of document",
      "type": "string"
    },
    "keywords": {
      "default": [],
      "items": {
        "type": "string"
      },
      "title": "Possible keywords",
      "type": "array"
    },
    "abstract": {
      "default": "",
      "title": "Abstract of the paper",
      "type": "string"
    },
    "body": {
      "default": "",
      "title": "Optional body of document",
      "type": "string"
    }
  },
  "required": [
    "docid",
    "published",
    "title",
    "authors",
    "url"
  ],
  "title": "Document",
  "type": "object"
}
```

The search index itself indexes all fields sent to it, and when you
query the database you get most of the document back for every hit on
the index.  The only exception is the `body` part, which can be quite
large and is therefore omitted. If you are intending to create
context-sensitive search snippets, you should be aware that a term hit
can occur in the body. At present all terms are 'anded' together, so
if you supply a spurious term you will get no results unless it
matches a prefix of a term.

## The REST API

The server is set up to maintain multiple indices that are named in
config['XAPIAN_PATHS']. There is a query parameter `'c'` that can be
used to specify which search index to reference. If it is not specified,
then it falls back to `'default'`.

The REST API is very simple, providing only two capabilities:
1. a GET to `/search?q=query` will execute a search using `query` as the text query.
2. a POST to /index with a JSON body will add documents to the index. The payload
   should contain a `papers` array containing a list of documents to be indexed.
   The schema for the papers should follow the schema of `Document` in
   `searchapp/index/model.py`. That schema should not be linked to the other
   python code because that would contaminate the license of the other code. 

Only the POST is authenticated, so don't use this for sensitive
documents.  In both cases you can supply the `'c'` parameter to select
the index.


## Search quality

The search using xapian is only rudimentary. I've taken the approach
that all terms are "anded" together. There are lots of things under
the covers that could be exploited, but I wanted something simple. For
some reason many people ignore search and prefer to just use "Ctrl-F"
in their browser to search a gigantic web page. Bad habits die hard. 🤡

### Performance and alternatives

There are lots of search alternatives, but very little that makes
sense to run locally. I generally hate remote services because they
jerk you around with API changes, service changes, "code of conduct"
changes, etc. The xapian library is disk-based, so it imposes very
little memory load on the server (unlike elastic search, solr, and
lucene, which are absolute pigs requiring a lot of resources). xapian
is fast enough to serve autocomplete functionality (under 50ms for
millions of documents). Performance on inverted keyword indices can be
hard to predict, but a rough idea is that it needs to fetch a posting
list for each term and then join them together. There is a rule of
thumb called [Heaps' law](https://en.wikipedia.org/wiki/Heaps%27_law)
that suggests you would expect to have sqrt(n) terms in a corpus of n
documents. This tells you roughly the number of posting lists to
expect. Obviously some words like 'the' will occur in almost every
document, but xapian has a default list of stopwords. Good luck
searching for the band ['The
The'](https://en.wikipedia.org/wiki/The_The).

### Future refinements.

I'm not really interested in piling every feature into this simple
server.  If you want to expand this server, then consider using this
as a guide for how to get started, or else just fork it and add your
own features. If you want something more sophisticated, consider using
[Omega](https://xapian.org/docs/omega/overview.html) that is provided
by the xapian project. It has features for parsing documents before
ingesting them in the database, and provides some multi-lingual
support.

In the future I may support 'faceted search' that allows you to
retrict the query to specific fields like 'author'. We may also
provide range search on the 'published' field. It's also conceivable
that `model.Document` may support things like categories. We may also
provide control over things like stemming, prefix search, phrase
queries, 'near' queries, boolean operands, etc. For now let's keep it
simple.