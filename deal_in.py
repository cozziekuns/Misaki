import re

import numpy as np
import lightgbm as lgb

TILE_SUITS = {
    'm': 0,
    'p': 1,
    's': 2,
    'z': 3,
}

TILE_SUIT_ARRAY = ['m', 'p', 's', 'z']

def stringify_tile(tile):
  value = tile % 9 + 1
  suit = TILE_SUIT_ARRAY[tile // 9]

  return str(value) + str(suit)

MODELS = [
    lgb.Booster(model_file=f'./static/models/deal_in/full_{stringify_tile(i)}.model')
    for i in range(0, 34)
]

def parse_tile(tile_string):
    value = int(tile_string[0]) - 1
    suit_offset = 9 * TILE_SUITS[tile_string[1]]

    return suit_offset + value

def parse_hand_string(hand_string):
    return [parse_tile(tile_string) for tile_string in re.findall('..', hand_string)]

def get_deal_in_probs(discards_string):
    discards = parse_hand_string(discards_string)

    packed_discards = [
        discards[i] + 1 if i < len(discards) else 0
        for i in range(0, 24)
    ]

    deal_in_probs = [
        MODELS[i].predict(np.array([packed_discards]))[0] 
        for i in range(0, 34)
    ]

    return deal_in_probs
