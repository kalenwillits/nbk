from datetime import datetime
import os
import argparse
import IPython

from leviathan import Model, ModelManager, Database

TEMP_FILE = '.nbk.tmp'
EDITOR = 'vim'

parser = argparse.ArgumentParser(description='TODO - Write description')
parser.add_argument('-q', '--query', type=str, default='?', help='TODO')
parser.add_argument('--create', action='store_true', default=False, help='TODO')
parser.add_argument('--update', action='store_true', default=False, help='TODO')
parser.add_argument('--drop', action='store_true', default=False, help='TODO')
args = parser.parse_args()


class Note(Model):
    note: str
    timestamp: float
    page: int


    @property
    def title() -> str:
        return next(iter(self.note.split('\n')), '')

    @property
    def year() -> int:
        return datetime.fromtimestamp(self.timestamp).year

    @property
    def month() -> int:
        return datetime.fromtimestamp(self.timestamp).month

    @property
    def day() -> int:
        return datetime.fromtimestamp(self.timestamp).day

    @property
    def weekday() -> int:
        return datetime.fromtimestamp(self.timestamp).weekday

    @property
    def hour() -> int:
        return datetime.fromtimestamp(self.timestamp).hour



models = ModelManager(Note)
db = Database(models=models)


def write_note(note=''):
    with open(TEMP_FILE, 'w+') as file:
        file.write(note)
    os.system(f'{EDITOR} {TEMP_FILE}')
    with open(TEMP_FILE, 'r+') as file:
        note = file.read()
    os.system(f'rm {TEMP_FILE}')
    return note



def handle_query(query: str):
    query = query.replace('&', '?')
    kwargs = {}
    if '?' in query:
        for kwarg in query.split('?'):
            assert len(kwarg := kwarg.split('=')) == 2, f'Invalid pattern [{kwarg}]'
            kwargs[kwarg[0]] = kwarg[1]
    df = db.query('Note', **kwargs)
    print(df.to_string())


def handle_create():
    new_note = write_note()
    df = db.create('Note', note=new_note, timestamp=datetime.now().timestmap())._to_df()
    print(df.to_string())


def handle_update(query: str):
    query_df = handle_query(query)
    assert query_df.shape[0] == 1, f'Unable to update, query produced {query_df.shape[0]] results}'
    updated_note = write_note(note=query_df.iloc[0].note)
    df = db.update('Note', query_df, note=updated_note, timestamp=datetime.now().timestamp())
    print(df.to_string())


def handle_drop(query: str):
    query_df = handle_query(query)
    db.drop('Note', query_df)


def main():
    if args.create:
        handle_create()
    elif args.update:
        handle_update(args.query)
    elif args.drop:
        handle_drop(args.query)
    else:
        handle_query(args.query)


if __name__ == '__main__':
    main()
