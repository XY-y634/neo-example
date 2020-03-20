from neomodel import config, db
from neomodel import remove_all_labels, install_all_labels, clear_neo4j_database
from neomodel import Property, StructuredNode
from neomodel import BooleanProperty, StringProperty, DateProperty


class Graph:
    def __init__(self, uri='bolt://neo4j:123456@10.71.115.8:7687', install_labels=True):
        config.DATABASE_URL = uri
        config.AUTO_INSTALL_LABELS = True
        self.bind_merge_method()
        if install_labels:
            install_all_labels()

    def reset(self, reset_labels=False):
        print('Delete all nodes and relationships...')
        if reset_labels:
            remove_all_labels()
            install_all_labels()
        clear_neo4j_database(db)

    @staticmethod
    def bind_merge_method():
        def merge(self):
            def cypher_value(key):
                property = properties[key]
                if isinstance(property, DateProperty):
                    return '\''+deflated_params[key]+'\''
                elif isinstance(property, StringProperty):
                    return '\''+deflated_params[key]+'\''
                elif isinstance(property, BooleanProperty):
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
                query += "WHERE " + " OR ".join(["n.{0}={1}".format(Pkey, cypher_value(Pkey)) for Pkey in primary_keys]) + "\n"
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

    def create_sample_data(self, reset=True):
        from random import random, randint, choice, sample
        from datetime import date
        from src.models.neo4j_models import Paper, Author, Journal

        if reset:
            self.reset(reset_labels=True)
        print('Create sample data...')
        get_pmid = lambda _: choice(['60'+'%03d'%i for i in range(400)])
        get_words = lambda x: ' '.join(sample(['Hello', 'World', 'Great', 'Neo4j', 'Project', '.']*5, x))
        get_date = lambda _: date(1990+randint(1,20), randint(1,12), randint(1,28))

        for article_index in range(randint(8, 12)):
            pmid = get_pmid(0)
            print(f'Create relationship with article {article_index+1}:{pmid}...')
            journal = Journal(epub_issn=get_words(3)).merge()
            article = Paper(
                pmid=pmid,
                doi=get_pmid(0) if random()>0.8 else '',
                title=get_words(randint(5, 8)),
                date=get_date(0),
                date_type="emmm"
            ).merge()
            article.publish_on.connect(journal)

            for refer_index in range(randint(10, 20)):
                reference = Paper(pmid=get_pmid(0), date=get_date(0), date_type="emmm").merge()
                reference.cited_by.connect(article)
            for refer_index in range(randint(10, 20)):
                reference = Paper(pmid=get_pmid(0), date=get_date(0), date_type="emmm").merge()
                reference.cited_by.connect(article)
            for author_index in range(randint(1, 8)):
                author = Author(name=get_words(4), surname=get_words(2)).merge()
                author.wrote.connect(article, {'affiliation': get_words(20)})

    @staticmethod
    def dataframe(data, columns):
        import pandas as pd
        return pd.DataFrame(data, columns=columns)

    def query_test(self):
        from src.models.neo4j_models import Paper
        results, columns = db.cypher_query("""\
        MATCH ()-[r:REFER]->(a:Article)
        WITH a, COUNT(r) as count
        RETURN a, count
        ORDER BY count DESC LIMIT 1
        """)
        article = Paper.inflate(results[0][0])
        print(f'Article(pmid={article.pmid}) has most edges({results[0][1]})')
        # print(article.references)
        # print(self.dataframe(results, columns))


if __name__ == '__main__':
    g = Graph(uri='bolt://neo4j:zxh123@10.10.119.189:7687')
    g.reset(reset_labels=True)
    g.create_sample_data(reset=False)
    g.query_test()
    # g.some_test()

    print('Done!')
