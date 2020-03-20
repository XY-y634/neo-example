from src.neo4human.utilities import Graph, db


Graph('localhost:7687', install_labels=False)

results, columns = db.cypher_query("CREATE (a:A {name:'NodeA'}) RETURN a")
node = results[0][0]
print(node)
print(type(node))

assert node.labels == {'A'}
assert node['name'] == 'NodeA'

# Clean the test node
db.cypher_query("MATCH (a:A {name:'NodeA'}) DELETE a")
