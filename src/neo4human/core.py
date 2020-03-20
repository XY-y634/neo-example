import re
import sys
from neomodel import db
from neomodel.relationship_manager import check_source, OUTGOING, INCOMING
from neomodel import OneOrMore as LegacyOneOrMore
from neomodel.match import NodeSet, QueryBuilder
from neomodel import classproperty


"""
Some module of neomodel is not yet compatible with neo4j>= 4.0
This file is dedicated to correct these syntax.
Some day in the future these bugs may be fixed in official release,
    but not now, this is it.
"""


def drop_constraints(quiet=True, stdout=None):
    """
    Discover and drop all constraints.

    :type: bool
    :return: None
    """

    results, meta = db.cypher_query("CALL db.constraints()")
    pattern = re.compile(':(.*) \).*\.(\w*)')
    for constraint in results:
        db.cypher_query('DROP CONSTRAINT ' + constraint[0])
        match = pattern.search(constraint[0])
        if match:
            stdout.write(''' - Droping unique constraint and index on label {0} with property {1}.\n'''.format(
                match.group(1), match.group(2)))


def drop_indexes(quiet=True, stdout=None):
    """
    Discover and drop all indexes.

    :type: bool
    :return: None
    """

    results, meta = db.cypher_query("CALL db.indexes()")
    pattern = re.compile(':(.*)\((.*)\)')
    for index in results:
        db.cypher_query('DROP INDEX ' + str(index[1]))
        match = pattern.search(index[1])
        if match:
            stdout.write(' - Dropping index on label {0} with property {1}.\n'.format(
                match.group(1), match.group(2)))


def remove_all_labels(stdout=None):
    """
    Calls functions for dropping constraints and indexes.

    :param stdout: output stream
    :return: None
    """

    if not stdout:
        stdout = sys.stdout

    stdout.write("Droping constraints...\n")
    drop_constraints(quiet=False, stdout=stdout)

    stdout.write('Droping indexes...\n')
    drop_indexes(quiet=False, stdout=stdout)


def _rel_helper(lhs, rhs, ident=None, relation_type=None, direction=None, relation_properties=None, **kwargs):
    if direction == OUTGOING:
        stmt = '-{0}->'
    elif direction == INCOMING:
        stmt = '<-{0}-'
    else:
        stmt = '-{0}-'

    rel_props = ''

    if relation_properties:
        rel_props = ' {{{0}}}'.format(', '.join(
            ['{0}: ${1}'.format(key, value[1:-1]) for key, value in relation_properties.items()]))

    # direct, relation_type=None is unspecified, relation_type
    if relation_type is None:
        stmt = stmt.format('')
    # all("*" wildcard) relation_type
    elif relation_type == '*':
        stmt = stmt.format('[*]')
    else:
        # explicit relation_type
        stmt = stmt.format('[{0}:`{1}`{2}]'.format(ident if ident else '', relation_type, rel_props))

    return "({0}){1}({2})".format(lhs, stmt, rhs)


class Neo4QueryBuilder(QueryBuilder):
    def build_node(self, node):
        ident = node.__class__.__name__.lower()
        place_holder = self._register_place_holder(ident)

        # Hack to emulate START to lookup a node by id
        _node_lookup = 'MATCH ({0}) WHERE id({1})=${2} WITH {3}'.format(ident, ident, place_holder, ident)
        self._ast['lookup'] = _node_lookup

        self._query_params[place_holder] = node.id

        self._ast['return'] = ident
        self._ast['result_class'] = node.__class__
        # print(ident)
        return ident

    def build_query(self):
        query = ''

        if 'lookup' in self._ast:
            query += self._ast['lookup']

        if self._ast['match']:
            query += ' MATCH '
            query += ', '.join(['({0})'.format(i) for i in self._ast['match']])

        if 'where' in self._ast and self._ast['where']:
            query += ' WHERE '
            query += ' AND '.join([re.sub('\{(.*?)\}', r'$\1', x) for x in self._ast['where']])

        if 'with' in self._ast and self._ast['with']:
            query += ' WITH '
            query += self._ast['with']

        query += ' RETURN ' + self._ast['return']

        if 'order_by' in self._ast and self._ast['order_by']:
            query += ' ORDER BY '
            query += ', '.join(self._ast['order_by'])

        if 'skip' in self._ast:
            query += ' SKIP {0:d}'.format(self._ast['skip'])

        if 'limit' in self._ast:
            query += ' LIMIT {0:d}'.format(self._ast['limit'])

        return query


class Neo4NodeSet(NodeSet):
    query_cls = Neo4QueryBuilder


@classproperty
def nodes(cls):
    return Neo4NodeSet(cls)


class OneOrMore(LegacyOneOrMore):
    @check_source
    def connect(self, node, properties=None):
        self._check_node(node)

        if not self.definition['model'] and properties:
            raise NotImplementedError(
                "Relationship properties without using a relationship model "
                "is no longer supported."
            )

        params = {}
        rel_model = self.definition['model']
        rp = None  # rel_properties

        if rel_model:
            rp = {}
            # need to generate defaults etc to create fake instance
            tmp = rel_model(**properties) if properties else rel_model()
            # build params and place holders to pass to rel_helper
            for p, v in rel_model.deflate(tmp.__properties__).items():
                rp[p] = '{' + p + '}'
                params[p] = v

            if hasattr(tmp, 'pre_save'):
                tmp.pre_save()

        new_rel = _rel_helper(lhs='us', rhs='them', ident='r', relation_properties=rp, **self.definition)
        # Changed this line for neo4j >= 4.0
        q = "MATCH (them), (us) WHERE id(them)=$them and id(us)=$self " \
            "MERGE " + new_rel

        params['them'] = node.id

        if not rel_model:
            self.source.cypher(q, params)
            return True

        rel_ = self.source.cypher(q + " RETURN r", params)[0][0][0]
        rel_instance = self._set_start_end_cls(rel_model.inflate(rel_), node)

        if hasattr(rel_instance, 'post_save'):
            rel_instance.post_save()

        return rel_instance
