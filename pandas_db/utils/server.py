from datetime import datetime


def on_connect(ws=None, sv=None, db=None):
    '''
    Placeholder that runs after a websocket connection starts and is authenticated.
    '''
    ...


def on_disconnect(ws=None, sv=None, db=None):
    '''
    Placeholder that runs after a websocket disconnets.
    '''
    ...


def on_log(ws=None, sv=None, db=None, status=None, data=None, error=None):
    # TODO - Make better
    if sv.debug:
        print(str(datetime.now()), f'[{status}]', data)
