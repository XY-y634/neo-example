from src.neo4human.utilities import Graph, reset_db
from src.models import Paper
from datetime import date


Graph('localhost:7687', install_labels=False)
reset_db(confirmed=True)

print()
print('Creating node...')
article = Paper(
    pmid='6327467',
    doi='',
    title='From Biomedical NER to KG: A Great Article.',
    date=date.today(),
    date_type='epub'
)

# Before merge, Nodes DO NOT have `id`
print('article has id:', hasattr(article, 'id'))

article.merge()
print('article id after merge:', article.id)

query_article = Paper.nodes.get_or_none(pmid=article.pmid)
assert query_article == article

print()
print('Deleting this node...')
article.delete()
print(Paper.nodes.get_or_none(pmid=article.pmid))
