print('Running all three examples at once:')

print('-'*64)
print('-> Test 1/3  | BASIC CYPHER')
from src.examples import basic_cypher

print('-'*64)
print('-> Test 2/3  | BASIC MODEL')
from src.examples import basic_model

print('-'*64)
print('-> Test 3/3  | CREATE COMPLEX GRAPH')
from src.examples import create_complex_graph

print('All tests working nicely!')
