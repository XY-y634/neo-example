from src.models.neo_renaming import *
from src.models.neomerge import Graph, install_all_labels

from src.models.mongo_models import *
from neomodel.exceptions import UniqueProperty
from datetime import datetime


# mongoexport --host="127.0.0.1:27017" --collection=paper --db=Anti-Aging
# --out=export/paper.csv --type=csv --fields=_id,pmcid,doi,title,date,date_type


# LOAD CSV WITH HEADERS FROM 'file:///paper.csv' AS row
# WITH row WHERE row._id IS NOT NULL
# MERGE (p:Paper {pmid: row._id, title:row.title, date:row.date, date_type:row.date_type})
# ON CREATE SET p.pmcid = row.pmcid
# ON MATCH SET p.pmcid = row.pmcid
# ON CREATE SET p.doi = row.doi
# ON MATCH SET p.doi = row.doi


def get_primary_key_name(obj):
    for field_name in obj:
        field = obj._fields.get(field_name)
        if field.primary_key:
            return field_name


def inflate_date(properties):
    for k, v in properties.items():
        if isinstance(v, datetime):
            properties[k] = v.date()
    return properties


def mongo_to_neo4j_obj(me, id_alias=None):
    if not id_alias:
        id_alias = get_primary_key_name(me)
    properties = me.to_mongo().to_dict()
    # print(properties)
    properties[id_alias] = properties['_id']
    if id_alias != '_id':
        del properties['_id']
    _properties = {}
    for k, v in properties.items():
        if k and k[0] != '_':
            _properties[k] = v
    return inflate_date(_properties)


def reset_neo_sync(*mongo_clses):
    for mongo_cls in mongo_clses:
        mongo_cls.objects.filter(_neo_synced=True).update(_neo_synced=False)
        print(f'All neo_sync tag reset on {mongo_cls.__name__} successfully!')


def sync_mongo_nodes_to_neo4j(node_me_cls, node_neo_cls, custom_id_alias=None, batch_size=500):
    item_batch = node_me_cls.objects.filter(_neo_synced__ne=True).limit(batch_size)
    if not item_batch:
        exit()
    ori_id_alias = get_primary_key_name(item_batch[0])
    id_alias = custom_id_alias if custom_id_alias else ori_id_alias
    while item_batch:
        print(item_batch[0][ori_id_alias])
        conflict_count = 0
        for item in item_batch:
            try:
                obj_dict = mongo_to_neo4j_obj(item, id_alias)
                # print(obj_dict)
                node_neo_cls(**obj_dict).save()
            except UniqueProperty:
                conflict_count += 1
            item.update(_neo_synced=True)
        if conflict_count != 0:
            print(f'Conflicts ({conflict_count}) on primary key found, skipping...')
        item_batch = node_me_cls.objects.filter(_neo_synced__ne=True).limit(batch_size)


def sync_mongo_relations_to_neo4j(mongo_rel, neo_obj, neo_sub, obj_ids, sub_ids, rel_name,
                                  batch_size=500, relation_args=()):
    item_batch = mongo_rel.objects.filter(_neo_synced__ne=True).limit(batch_size)
    obj_id, obj_rel_id = obj_ids
    sub_id, sub_rel_id = sub_ids
    while item_batch:
        print(mongo_to_neo4j_obj(item_batch[0]))
        conflict_count = 0
        for item in item_batch:
            item_dict = mongo_to_neo4j_obj(item)
            try:
                obj = neo_obj.nodes.get(**{obj_id: item_dict[obj_rel_id]})
                sub = neo_sub.nodes.get(**{sub_id: item_dict[sub_rel_id]})
                assert obj and sub
                relation_kwargs = {x: item_dict.get(x) for x in relation_args}
                getattr(obj, rel_name).connect(sub, relation_kwargs)
            except UniqueProperty:
                conflict_count += 1
            except Exception as e:
                print('Error:', item_dict)
                print(e)
                # exit()
            item.update(_neo_synced=True)
            item.save()
        if conflict_count != 0:
            print(f'Conflicts ({conflict_count}) on primary key found, skipping...')
        item_batch = mongo_rel.objects.filter(_neo_synced__ne=True).limit(batch_size)


DB_ADDR = '127.0.0.1'  # 10.10.119.189

g = Graph('bolt://neo4j:zxh123@'+DB_ADDR+':7687', install_labels=True)
# g.reset(reset_labels=True)

connect(db='Anti-Aging', host='mongodb://'+DB_ADDR+':27017/')


reset_neo_sync(PaperPaper)

# sync_mongo_relations_to_neo4j(
#     PaperAuthor, Paper_, Author_,
#     ('pmid', 'paper'), ('full_name', 'author'), 'authors',
#     relation_args=['affiliation']
# )
# sync_mongo_relations_to_neo4j(
#     PaperPaper, Paper_, Paper_,
#     ('pmid', 'paper_ori'), ('pmid', 'paper_use'), 'cited_by'
# )
sync_mongo_relations_to_neo4j(
    PaperEntity, Paper_, Entity_,
    ('pmid', 'paper'), ('name', 'entity'), 'entities',
    relation_args=['count']
)
sync_mongo_relations_to_neo4j(
    PaperJournal, Paper_, Journal_,
    ('pmid', 'paper'), ('issn', 'journal'), 'publish_on'
)
sync_mongo_relations_to_neo4j(
    PaperPubType, Paper_, PubType_,
    ('pmid', 'paper'), ('name', 'pub_type'), 'pub_types'
)

# sync_mongo_nodes_to_neo4j(Entity, Entity_, custom_id_alias='name')
# sync_mongo_nodes_to_neo4j(Paper, Paper_)
# sync_mongo_nodes_to_neo4j(PubType, PubType_)
# sync_mongo_nodes_to_neo4j(Journal, Journal_)
# sync_mongo_nodes_to_neo4j(Author, Author_)
