# cicsearch

This repository contains code for the search functionality of
cic.iacr.org, but it can be used for anything whose documents can be
converted to the `model.Document` class.  This uses the [xapian
library](https://xapian.org/) to provide this capability.  Because the
xapian library is [only licensed under the GPL
license](https://trac.xapian.org/wiki/Licensing), this repository must
also be licensed that way. It is bundled separately here in order to
prevent contamination of any code that uses it. Communication to this
library is only through REST API calls, and this library should not be
linked with anything unless it is also licensed under GPL.

The server can also be used by two different apps, because it
maintains two different xapian indices depending on whether the 'd'
flag is used in queries.

The REST API is very simple, providing only two capabilities:
1. a GET to `/search?q=query` will execute a search using `query` as the query.
2. a POST to /index with a JSON body will add documents to the index. The payload
   should contain a `papers` array containing a list of documents to be indexed.
   The schema for the papers should follow the schema of `Document` in
   `searchapp/index/model.py`. That schema should not be linked to the other
   python code because that would contaminate the license of the other code.

## Document schema

The json schema for the document format is:
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
