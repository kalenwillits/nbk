from datetime import datetime
import os
import argparse
import IPython
from uuid import uuid4

from pandas_db import Model, ModelManager, Database
from pandas_db.utils import is_numeric

from pyperclip import copy
import tabulate   # imported only to be included when compiled.

# TODO - Reset title on update
# TODO - migrate page number at some point
# TODO - Add reletive dates -r --recent
# TODO - breakup -s to -cp --copy and -s --subsitute
# TODO - Add -e --execute to execute note as a bash script. This will allow workflow automations
EDITOR = 'vim'
DATA_PATH = os.path.join('home', os.getlogin(), 'nbk', 'data')

parser = argparse.ArgumentParser(description='TODO - Write description')

#  nargs='?': Allows the positional argument to be optional.
parser.add_argument('query', type=str, default='', nargs='?', help='TODO')
parser.add_argument('-c', '--create', action='store_true', default=False, help='TODO')
parser.add_argument('-u', '--update', action='store_true', default=False, help='TODO')
parser.add_argument('-d', '--drop', action='store_true', default=False, help='TODO')
parser.add_argument('-s', '--snippet', help='TODO')
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
    print(df[['title', 'timestamp']].to_markdown())
    if df.shape[0] == 1:
        print(df.note.iloc[0])


def handle_snippet(query: str, format_value: str):
    query_df = handle_query(query)
    format_value_list = format_value.split('&')
    assert query_df.shape[0] == 1, f'Unable to get snippet, query produced {query_df.shape[0]} results'
    if format_value is not None:
        formatted_note = query_df.iloc[0].note.format(*format_value_list)
        formatted_note_with_no_title = formatted_note.split('\n', 1)[1]
        copy(formatted_note_with_no_title)
    else:
        copy(query.iloc[0].note.split('\n', 1))


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
    confirm = input(f'This action will delete {df.shape[0]} notes, are you sure? [y/n] ').lower()
    if confirm == 'y' or confirm == 'yes':
        db.drop('Note', df)
        db.save()


def handle_shell():
    IPython.embed()


def main():
    if args.shell:
        handle_shell()
    elif args.snippet:
        handle_snippet(args.query, args.snippet)
    elif args.create:
        handle_create()
    elif args.update:
        handle_update(args.query)
    elif args.drop:
        handle_drop(args.query)
    else:
        output(handle_query(args.query))


if __name__ == '__main__':
    main()
