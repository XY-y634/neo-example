from random import random, randint, choice, sample
from datetime import date
import sys
from time import sleep
from src.models import Paper, Author, Journal
from src.neo4human import Graph, reset_db, create_labels, table_view


Graph('localhost:7687', install_labels=False)
reset_db(confirmed=True)
create_labels()


def get_pmid():
    return choice(['60'+'%03d' % i for i in range(400)])


def get_words(x):
    return ' '.join(sample(['Hello', 'World', 'Great', 'Neo4j', 'Project', '.']*5, x))


def get_date():
    return date(1990+randint(1, 20), randint(1, 12), randint(1, 28))


print('Creating sample data...')

for article_index in range(randint(8, 12)):
    pmid = get_pmid()
    print(f'Create relationship with article {article_index+1}:{pmid}...')
    journal = Journal(issn=get_words(3)).merge()
    article = Paper(
        pmid=pmid,
        # Some data may be missing
        doi=get_pmid() if random() > 0.8 else '',
        title=get_words(randint(5, 8)),
        date=get_date(),
        date_type="emmm"
    ).merge()
    article.publish_on.connect(journal)

    for refer_index in range(randint(10, 20)):
        reference = Paper(pmid=get_pmid(), date=get_date(), date_type="emmm").merge()
        reference.cited_by.connect(article)
    for refer_index in range(randint(10, 20)):
        reference = Paper(pmid=get_pmid(), date=get_date(), date_type="emmm").merge()
        reference.cited_by.connect(article)
    for author_index in range(randint(1, 8)):
        author = Author(full_name=get_words(4), surname=get_words(2)).merge()
        author.wrote.connect(article, {'affiliation': get_words(20)})


print('Generated graph successfully!')

print()
print('Querying the top 3 cited paper:')
table_view("""\
MATCH ()-[r:REFER]->(a:Paper)
WITH a, COUNT(r) as count
RETURN a.pmid, count
ORDER BY count DESC LIMIT 3
""")

print()
sleep(0.1)
print('Run the following query in the browser to view the result:', file=sys.stderr)
print('$ MATCH (n) RETURN n LIMIT 300', file=sys.stderr)
