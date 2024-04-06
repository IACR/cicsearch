"""
This contains the data model for indexed documents. Do not link
this to other code.
"""

from pydantic import StringConstraints, BaseModel, Field
from typing import List
from typing_extensions import Annotated

date_regex = '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'
class Document(BaseModel):
    """The model of a document to be indexed."""
    docid: str = Field(...,
                    title='Globally unique document ID')
    published: Annotated[str, StringConstraints(pattern=date_regex)] = Field(...,
                                                                             title='Date of publication')
    title: Annotated[str, StringConstraints(min_length=2)] = Field(...,
                                                                   title='The title of the document')
    authors: List[str] = Field(...,
                               title='List of author names')
    url: str = Field(...,
                     title='URL of document')
    keywords: List[str] = Field([],
                                title='Possible keywords')
    abstract: str = Field('',
                          title='Abstract of the paper')
    body: str = Field('',
                      title='Optional body of document')


if __name__ == '__main__':
    import json
    print(json.dumps(Document.model_json_schema(), indent=2))
