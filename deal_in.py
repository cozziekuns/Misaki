import re

import numpy as np
import lightgbm as lgb

MAX_DISCARDS = 21

TILE_SUITS = {
    'm': 0,
    'p': 1,
    's': 2,
    'z': 3,
}

MODIFIERS = {
    't': 0,
    'T': 1,
    'r': 2,
    'R': 3,
}

TILE_SUIT_ARRAY = ['m', 'p', 's', 'z']

def stringify_tile(tile):
  value = tile % 9 + 1
  suit = TILE_SUIT_ARRAY[tile // 9]

  return str(value) + str(suit)

MODELS = [
    lgb.Booster(model_file=f'./static/models/deal_in_complex/full_{stringify_tile(i)}.model')
    for i in range(0, 34)
]

def parse_tile(tile_string):
    value = int(tile_string[0]) - 1
    suit_offset = 9 * TILE_SUITS[tile_string[1]]

    return suit_offset + value + 1

def parse_tile_with_modifier(tile_string):
    return parse_tile(tile_string[0:2]), MODIFIERS[tile_string[2]] 

def parse_discards_string(discards_string):
    return [
        parse_tile_with_modifier(tile_string)
        for tile_string in re.findall('...', discards_string)
    ]

def get_deal_in_probs(dora_string, discards_string):
    dora = parse_tile(dora_string)

    discards = parse_discards_string(discards_string)

    packed_discards = [discard[0] for discard in discards] + [0] * (MAX_DISCARDS - len(discards))
    packed_tedashi = [discard[1] % 2 + 1 for discard in discards] + [0] * (MAX_DISCARDS - len(discards))
    riichi_tile_index = next(i for i, v in enumerate(discards) if v[1] >= 2) + 1

    input_vector = [dora] + packed_discards + packed_tedashi + [riichi_tile_index]

    deal_in_probs = [
        MODELS[i].predict(np.array([input_vector]))[0] 
        for i in range(0, 34)
    ]

    return deal_in_probs
