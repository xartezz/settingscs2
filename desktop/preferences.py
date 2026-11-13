"""Stable game preference storage, separate from supported config workflows."""
import json
GAMES = ('cs2', 'fivem')

def parse_games(raw):
    try:
        values=json.loads(raw)
    except (ValueError,TypeError):return []
    if not isinstance(values,list):return []
    return [game for game in GAMES if game in values]

def serialize_games(values):
    selected=[game for game in GAMES if game in values]
    if not selected:raise ValueError('Choose at least one game to continue.')
    return json.dumps(selected)
