from datetime import datetime, timedelta
import os
import argparse
import IPython
import json
from uuid import uuid4

from pandas_db import Model, ModelManager, Database
from pandas_db.utils import is_numeric

from pyperclip import copy
import tabulate   # imported only to be included when compiled.

CONFIG_FILE = 'config.json'
DEFAULT_CONFIG = {'EDITOR': 'vim'}

global config

if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'w') as json_config_file:
        json_config_file.write(json.dumps(DEFAULT_CONFIG))

with open(CONFIG_FILE) as json_config_file:
    config = json.loads(json_config_file.read())

if config.get('DATA_PATH') is None:
    config['DATA_PATH'] = os.path.join('home', os.getlogin(), 'nbk', 'data')

TODAY = datetime.now()

parser = argparse.ArgumentParser(description='Simple terminal notes organizer and utility system.')

#  nargs='?': Allows the positional argument to be optional.
parser.add_argument('query', type=str, default='', nargs='?', help='TODO')
parser.add_argument('-c', '--create', action='store_true', default=False, help='TODO')
parser.add_argument('-u', '--update', action='store_true', default=False, help='TODO')
parser.add_argument('-d', '--drop', action='store_true', default=False, help='TODO')
parser.add_argument('-s', '--snippet', help='TODO')
parser.add_argument('-e', '--execute', help='TODO')
parser.add_argument('--shell', action='store_true', default=False, help='TODO')

args = parser.parse_args()


class Note(Model):
    note: str
    timestamp: float
    page: int

    @classmethod
    def _get_field(cls, field_partial: str) -> str:
        return next(filter(lambda field_name: field_partial in field_name, cls()._schema.fields()), None)

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
db = Database(models=models, path=config['DATA_PATH'])
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


def get_snippit(query: str, format_value: str) -> str:
    query_df = handle_query(query)
    format_value_list = format_value.split(';')
    assert query_df.shape[0] == 1, f'Unable to get snippet, query produced {query_df.shape[0]} results'
    if format_value is not None:
        assert len(snippit := query_df.iloc[0].note.split('```')) > 1, 'This note does not have a valid snippit.'
        snippit = snippit[1]
        return snippit.format(*format_value_list)


def handle_snippet(query: str, format_value: str):
    copy(get_snippit(query, format_value))


def handle_execute(query: str, format_value: str):
    os.system(get_snippit(query, format_value))


def write_note(note=''):
    temp_file = build_temp_file()
    with open(temp_file, 'w+') as file:
        file.write(note)
    os.system(f'{config["EDITOR"]} {temp_file}')
    with open(temp_file, 'r+') as file:
        note = file.read()
    os.system(f'rm {temp_file}')
    return note


def renumber_pages():
    db.Note.reset_index(inplace=True)
    db.Note.page = db.Note.index
    db.Note.page = db.Note.page.apply(lambda page: page + 1)


def handle_query(query: str):
    query = query.replace('&', '?')
    kwargs = {}
    if '?' in query:
        for kwarg in query.split('?'):
            if kwarg:
                assert len(field_value := kwarg.split('=')) == 2, f'Invalid pattern [{kwarg}]'
                field_func_split = field_value[0].split('__')
                value = field_value[1]
                assert (field := Note._get_field(field_func_split[0])), 'Invalid partial lookup {kwarg[0]}'

                if len(field_func_split) > 1:
                    field += '__' + field_func_split[1]

                if is_numeric(value):
                    kwargs[field] = float(value)
                else:
                    kwargs[field] = value

    df = db.query('Note', **kwargs)
    return df


def handle_create():
    new_note = write_note()
    page = db.query('Note').shape[0] + 1
    timestamp = datetime.now().timestamp()
    df = db.create('Note', note=new_note, timestamp=timestamp, page=page)._to_df()
    renumber_pages()
    db.save()
    return df


def handle_update(query: str):
    query_df = handle_query(query)
    assert query_df.shape[0] == 1, f'Unable to update, query produced {query_df.shape[0]} results'
    updated_note = write_note(note=query_df.iloc[0].note)
    df = db.update('Note', query_df, note=updated_note, timestamp=datetime.now().timestamp())
    renumber_pages()
    db.save()
    return df


def handle_drop(query: str):
    df = handle_query(query)
    confirm = input(f'This action will delete {df.shape[0]} notes, are you sure? [y/n] ').lower()
    if confirm == 'y' or confirm == 'yes':
        db.drop('Note', df)
        renumber_pages()
        db.save()


def handle_default_view():
    output(db.query('Note', timestamp__gt=(TODAY - timedelta(days=1)).timestamp()))


def handle_shell():
    IPython.embed()


def main():
    if args.shell:
        handle_shell()
    elif args.snippet:
        handle_snippet(args.query, args.snippet)
    elif args.execute:
        handle_execute(args.query, args.execute)
    elif args.create:
        handle_create()
    elif args.update:
        handle_update(args.query)
    elif args.drop:
        handle_drop(args.query)
    elif args.query:
        output(handle_query(args.query))
    else:
        handle_default_view()


if __name__ == '__main__':
    main()
