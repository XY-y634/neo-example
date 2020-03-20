from neomodel import StructuredNode, StructuredRel
from neomodel import StringProperty, IntegerProperty, DateProperty
from neomodel import RelationshipFrom, RelationshipTo
from neomodel import OneOrMore


"""
Relation Models
"""


class PaperAuthor(StructuredRel):
    affiliation = StringProperty()


class PaperEntity(StructuredRel):
    count = IntegerProperty(default=1)
    db_ids = StringProperty()


"""
Node Models
"""


class Author(StructuredNode):
    full_name = StringProperty(unique_index=True, required=True)
    surname = StringProperty(required=True)
    wrote = RelationshipTo('Paper', 'WROTE', OneOrMore, model=PaperAuthor)


class Journal(StructuredNode):
    issn = StringProperty(unique_index=True, required=True)
    iso_abbr = StringProperty()
    nlmid = StringProperty()
    title = StringProperty()
    publish = RelationshipTo('Paper', "PUBLISH", OneOrMore)


class Entity(StructuredNode):
    name = StringProperty(unique_index=True, required=True)
    term = StringProperty(required=True)
    type = StringProperty(required=True)
    db_name = StringProperty(required=True)
    appears_in = RelationshipFrom('Paper', "APPEAR", OneOrMore, model=PaperEntity)


class PubType(StructuredNode):
    name = StringProperty(unique_index=True, required=True)
    papers = RelationshipFrom('Paper', "HAS_A", OneOrMore)


class Paper(StructuredNode):
    pmid = StringProperty(unique_index=True, required=True)
    pmcid = StringProperty(index=True)
    doi = StringProperty(index=True)
    ppr = StringProperty(index=True)
    title = StringProperty()
    date = DateProperty(required=True, index=True)
    date_type = StringProperty(required=True)

    publish_on = RelationshipFrom('Journal', "PUBLISH", OneOrMore)
    authors = RelationshipFrom('Author', "WRITE", OneOrMore, model=PaperAuthor)
    references = RelationshipTo("Paper", "REFER", OneOrMore)
    cited_by = RelationshipFrom("Paper", "REFER", OneOrMore)
    entities = RelationshipTo('Entity', "APPEAR", OneOrMore, model=PaperEntity)
    pub_types = RelationshipTo('PubType', "IS_A", OneOrMore)

