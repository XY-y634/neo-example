from mongoengine import *
from pymongo.errors import BulkWriteError, DuplicateKeyError


class BulkUpdatable:
    _neo_synced = BooleanField(default=False)

    @classmethod
    def insert_many(cls, ME_objects, warning=True):
        has_dup = False
        
        if len(ME_objects) == 0:
            print('Warning: length of the docs is 0.')
            return
        try:
            doc_list = [doc.to_mongo() for doc in ME_objects]
            cls._get_collection().insert_many(doc_list, ordered=False)
        except (BulkWriteError, DuplicateKeyError) as bwe:
            has_dup = True
            if warning:
                print("Batch Inserted on <%s> with some errors. "
                    "May be some duplicates were found and are skipped." % (cls.__name__))
        except Exception as e:
            print({'error': str(e)})
            raise e
        
        return has_dup


class CrawledInfo(Document, BulkUpdatable):
    paper_id = StringField(required=True)
    name = StringField(required=True)
    result = DynamicField(required=True)
    parsed = BooleanField(default=False)

    meta = {
        'indexes': [
            {'fields': ('paper_id', 'name'), 'unique': True}
        ]
    }


class DbPaper(Document, BulkUpdatable):
    _id = StringField(primary_key=True)
    type = StringField(options=["crawl", "cite", "preprint"])
    info = DynamicField()


class Paper(Document, BulkUpdatable):
    pmid = StringField(primary_key=True)
    pmcid = StringField()
    doi = StringField()
    ppr = StringField()
    title = StringField()
    date = DateField()
    date_type = StringField()


class Entity(Document, BulkUpdatable):
    _id = StringField(primary_key=True)
    term = StringField(required=True)
    type = StringField(required=True)
    db_name = StringField(required=True)


class PaperEntity(Document, BulkUpdatable):
    paper = ReferenceField(Paper, required=True)
    entity = ReferenceField(Entity, required=True)
    count = IntField(default=1)
    db_ids = ListField(StringField())
    meta = {
        'indexes': [
            {'fields': ('paper', 'entity'), 'unique': True}
        ]
    }


class PaperPaper(Document, BulkUpdatable):
    paper_ori = ReferenceField(Paper, required=True)
    paper_use = ReferenceField(Paper, required=True)
    meta = {
        'indexes': [
            {'fields': ('paper_ori', 'paper_use'), 'unique': True}
        ]
    }


class Error(Document, BulkUpdatable):
    task = StringField(required=True)
    info = StringField(required=True)
    meta_data = DynamicField()

    meta = {'allow_inheritance': True}


class ExtractError(Error):
    task = StringField(default='extract')
    paper = ReferenceField(Paper, required=True)


class Warning(Document, BulkUpdatable):
    task = StringField(required=True)
    info = StringField(required=True)
    meta_data = DynamicField()

    meta = {'allow_inheritance': True}


class ExtractWarning(Warning):
    task = StringField(default='extract')
    paper = ReferenceField(Paper, required=True)


class PubType(Document, BulkUpdatable):
    name = StringField(primary_key=True)


class PaperPubType(Document, BulkUpdatable):
    paper = ReferenceField(Paper, required=True)
    pub_type = ReferenceField(PubType, required=True)
    meta = {
        'indexes': [
            {'fields': ('paper', 'pub_type'), 'unique': True}
        ]
    }


class Journal(Document, BulkUpdatable):
    issn = StringField(primary_key=True)
    title = StringField()
    nlmid = StringField()
    iso_abbr = StringField()


class PaperJournal(Document, BulkUpdatable):
    paper = ReferenceField(Paper, required=True)
    journal = ReferenceField(Journal, required=True)
    meta = {
        'indexes': [
            {'fields': ('paper', 'journal'), 'unique': True}
        ]
    }


class Author(Document, BulkUpdatable):
    full_name = StringField(primary_key=True)
    surname = StringField(required=True)
    _tmp_renamed = BooleanField(default=False)


class PaperAuthor(Document, BulkUpdatable):
    paper = ReferenceField(Paper, required=True)
    author = ReferenceField(Author, required=True)
    affiliation = StringField()
    _tmp_renamed = BooleanField(default=False)
    _new_flag = BooleanField(default=False)

    meta = {
        'indexes': [
            {'fields': ('paper', 'author'), 'unique': True}
        ]
    }
