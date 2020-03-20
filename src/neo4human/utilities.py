from neomodel import config, db
from neomodel import install_all_labels, clear_neo4j_database
# For neo4j <= 4.0, `remove_all_labels` should be imported from neomodel
from src.neo4human.core import remove_all_labels, nodes, delete
from neomodel import Property, StructuredNode
from neo4j.types.graph import Node
from neomodel import BooleanProperty, StringProperty, DateProperty


"""
Some functions to make life easier...

NOTICE: MERGE clause has changed in since Neo4j 4.0, 
        StructuredNode.merge may be useless in the future!
"""


def reset_db(reset_labels=True, confirmed=False):
    print('Deleting all nodes and relationships...')
    if not confirmed:
        confirm = input('Enter "Y" to confirm: ')
        confirmed = confirm == 'Y'
    if not confirmed:
        print('Reset canceled!')
        return
    if reset_labels:
        remove_all_labels()
    clear_neo4j_database(db)


def create_labels():
    print('Creating constrains...')
    install_all_labels()
    print('Created constrains in database:')
    results, columns = db.cypher_query("CALL db.constraints")
    [print(x) for x in results]


def merge(self):
    def cypher_value(key):
        _property = properties[key]
        if isinstance(_property, DateProperty):
            return '\'' + deflated_params[key] + '\''
        elif isinstance(_property, StringProperty):
            return '\'' + deflated_params[key] + '\''
        elif isinstance(_property, BooleanProperty):
            return str(deflated_params[key]).lower()
        else:
            return deflated_params[key]

    """
    Create or update(Cypher MERGE) functionality on a single new created node

    e.g.
    class Article(StructuredNode):
        title = StringProperty(unique_index=True, required=True)
        param = StringProperty()

    >>> article = Article(title='some title', param='value').merge()
    This line is translate into Cypher as:
        MERGE (a:Article {title: 'some title'})   SET a.param = 'value'    RETURN a

    :return: the node instance
    """
    props = self.__properties__
    deflated_params = self.deflate(props, skip_empty=True)
    properties = {attr: getattr(self.__class__, attr) for attr in dir(self.__class__)
                  if isinstance(getattr(self.__class__, attr), Property) and not attr.startswith("__")}
    node_keys = getattr(self.__class__, '__node_keys__', [])
    if node_keys:
        primary_keys = []
        for k, v in deflated_params.items():
            if v:
                if k in node_keys:
                    primary_keys.append(k)
            else:
                del vars(self)[k]
        primary_keys = [x for x in getattr(self.__class__, '__node_keys__')
                        if x in deflated_params and deflated_params[x]]
        query = "MATCH (n:{0})\n".format(':'.join(self.inherited_labels()))
        query += "WHERE " + " OR ".join(
            ["n.{0}={1}".format(Pkey, cypher_value(Pkey)) for Pkey in primary_keys]) + "\n"
        query += "RETURN n"
        node, _ = db.cypher_query(query)
        if not node or len(node[0]) == 0:
            return self.save()
        else:
            # or nodes should be combined
            assert len(node[0]) == 1
            self.id = self.inflate(node[0][0]).id
            return self.save()
    else:
        primary_keys = [k for k, v in properties.items() if v.unique_index]
        property_keys = [k for k, v in properties.items() if k not in primary_keys and k in deflated_params]
        query = "MERGE (n:{0} {{".format(':'.join(self.inherited_labels()))
        query += ", ".join(["{0}: {1}".format(Pkey, cypher_value(Pkey)) for Pkey in primary_keys]) + "})\n"
        query += 'ON CREATE SET ' + ', '.join(
            ['n.' + pkey + '=' + cypher_value(pkey) for pkey in property_keys]) + '\n' \
            if property_keys else ''
        query += "RETURN n"
        node, _ = db.cypher_query(query)
        assert len(node[0]) == 1
        self.id = self.inflate(node[0][0]).id
        return self


Property.composite_unique = False
Property.unique_or_null = False
StructuredNode.merge = merge
StructuredNode.nodes = nodes
StructuredNode.delete = delete


def table_view(query):
    import pandas as pd
    results, columns = db.cypher_query(query)
    for line in results:
        for index, item in enumerate(line):
            if isinstance(item, Node):
                line[index] = item.__repr__()
    print(pd.DataFrame(results, columns=columns))
    return results, columns


class Graph:
    def __init__(self, host, install_labels=True):
        config.DATABASE_URL = f'bolt://{self._auth}@{host}'
        config.AUTO_INSTALL_LABELS = True

        # For neo4j>=4.0, the following line is necessary
        # See this issue for more detail: https://github.com/neo4j-contrib/neomodel/issues/485
        config.ENCRYPTED_CONNECTION = False

        if install_labels:
            create_labels()

    @property
    def _auth(self):
        from os import path
        pass_file_path = path.join(path.abspath(__file__ + '/../../..'), '.neo_pass')
        return 'neo4j:'+open(pass_file_path).read().strip() if path.exists(pass_file_path) else ""
