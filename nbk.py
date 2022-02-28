from datetime import datetime
import os
import argparse
import IPython
from uuid import uuid4

from leviathan import Model, ModelManager, Database
from leviathan.utils import is_numeric

import tabulate   # imported only to be included when compiled.
from cmr import render

EDITOR = 'vim'
DATA_PATH = '/home/kalenwillits/nbk/data/'

parser = argparse.ArgumentParser(description='TODO - Write description')

#  nargs='?': Allows the positional argument to be optional.
parser.add_argument('query', type=str, default='', nargs='?', help='TODO')
parser.add_argument('-c', '--create', action='store_true', default=False, help='TODO')
parser.add_argument('-u', '--update', action='store_true', default=False, help='TODO')
parser.add_argument('-d', '--drop', action='store_true', default=False, help='TODO')
parser.add_argument('--shell', action='store_true', default=False, help='TODO')

args = parser.parse_args()


class Note(Model):
    note: str
    timestamp: float
    page: int

    @property
    def title(self) -> str:
        return next(iter(self.note.split('\n')), '')

    @property
    def year(self) -> int:
        return datetime.fromtimestamp(self.timestamp).year

    @property
    def month(self) -> int:
        return datetime.fromtimestamp(self.timestamp).month

    @property
    def day(self) -> int:
        return datetime.fromtimestamp(self.timestamp).day

    @property
    def weekday(self) -> int:
        return datetime.fromtimestamp(self.timestamp).weekday()

    @property
    def hour(self) -> int:
        return datetime.fromtimestamp(self.timestamp).hour


models = ModelManager(Note)
db = Database(models=models, path=DATA_PATH)
db.load()
db.migrate()


def build_temp_file():
    return f'.nbk-{uuid4()}.md'


def output(df):
    df.timestamp = df.timestamp.apply(lambda timestamp: str(datetime.fromtimestamp(timestamp).date()))
    df = df.set_index('page')
    print(render(df[['title', 'timestamp']].to_markdown()))
    if df.shape[0] == 1:
        print(render(df.note.iloc[0]))


def write_note(note=''):
    temp_file = build_temp_file()
    with open(temp_file, 'w+') as file:
        file.write(note)
    os.system(f'{EDITOR} {temp_file}')
    with open(temp_file, 'r+') as file:
        note = file.read()
    os.system(f'rm {temp_file}')
    return note


def handle_query(query: str):
    query = query.replace('&', '?')
    kwargs = {}
    if '?' in query:
        for kwarg in query.split('?'):
            if kwarg:
                assert len(kwarg := kwarg.split('=')) == 2, f'Invalid pattern [{kwarg}]'
                if is_numeric(kwarg[1]):
                    kwargs[kwarg[0]] = float(kwarg[1])
                else:
                    kwargs[kwarg[0]] = kwarg[1]
    df = db.query('Note', **kwargs)
    return df


def handle_create():
    new_note = write_note()
    page = db.query('Note').shape[0] + 1
    timestamp = datetime.now().timestamp()
    df = db.create('Note', note=new_note, timestamp=timestamp, page=page)._to_df()
    db.save()
    return df


def handle_update(query: str):
    query_df = handle_query(query)
    assert query_df.shape[0] == 1, f'Unable to update, query produced {query_df.shape[0]} results'
    updated_note = write_note(note=query_df.iloc[0].note)
    df = db.update('Note', query_df, note=updated_note, timestamp=datetime.now().timestamp())
    db.save()
    return df


def handle_drop(query: str):
    df = handle_query(query)
    db.drop('Note', df)
    db.save()


def handle_shell():
    IPython.embed()


def main():
    if args.shell:
        handle_shell()
    elif args.create:
        output(handle_create())
    elif args.update:
        output(handle_update(args.query))
    elif args.drop:
        handle_drop(args.query)
    else:
        output(handle_query(args.query))


if __name__ == '__main__':
    main()
