from operator import add, mul

import numpy as np
from xgboost import XGBClassifier
from game import Game_Agari

PERMUTATIONS = [
    [0, 1, 2, 3], [0, 1, 3, 2], [0, 2, 1, 3], [0, 2, 3, 1], [0, 3, 1, 2], [0, 3, 2, 1],
    [1, 0, 2, 3], [1, 0, 3, 2], [1, 2, 0, 3], [1, 2, 3, 0], [1, 3, 0, 2], [1, 3, 2, 0],
    [2, 0, 1, 3], [2, 0, 3, 1], [2, 1, 0, 3], [2, 1, 3, 0], [2, 3, 0, 1], [2, 3, 1, 0],
    [3, 0, 1, 2], [3, 0, 2, 1], [3, 1, 0, 2], [3, 1, 2, 0], [3, 2, 0, 1], [3, 2, 1, 0],
]

def calc_placement_ev(player_seat, kyoku, scores, payoff_matrix):
    prob_matrix = calc_prob_matrix(kyoku, scores)

    return np.dot(prob_matrix[player_seat], payoff_matrix)

def calc_prob_matrix(kyoku, scores):
    model = XGBClassifier()
    model.load_model('./static/models/full.model')

    input_vector = [kyoku] + scores
    probs = model.predict_proba(np.array([input_vector]))[0]

    totals = [
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]

    for i in range(0, 24):
        for j in range(0, 4):
            totals[j][PERMUTATIONS[i][j]] += probs[i]

    return totals

def solve_fold_player_draw(wall, player_draws, opp_draws, opp_waits):
    if player_draws == 0:
        return [0, 0, 0, 0, 0, 1]

    player_block_chance = opp_waits / wall
    advance_chance = 1 - player_block_chance

    block_matrix = solve_fold_opp_draw(wall - 1, player_draws - 1, opp_draws, opp_waits - 1)
    block_matrix = [player_block_chance * x for x in block_matrix]

    advance_matrix = solve_fold_opp_draw(wall - 1, player_draws - 1, opp_draws, opp_waits)
    advance_matrix = [advance_chance * x for x in advance_matrix]

    return list(map(add, block_matrix, advance_matrix))

def solve_fold_opp_draw(wall, player_draws, opp_draws, opp_waits):
    if opp_draws == 0:
        return [0, 0, 0, 0, 0, 1]

    opp_tsumo_chance = opp_waits / wall
    advance_chance = 1 - opp_tsumo_chance

    action_matrix = [0, 0, 0, opp_tsumo_chance, 0, 0]

    advance_matrix = solve_fold_player_draw(wall - 1, player_draws, opp_draws - 1, opp_waits)
    advance_matrix = [advance_chance * x for x in advance_matrix]

    return list(map(add, action_matrix, advance_matrix))

def solve_shoubu_player_draw(wall, player_draws, opp_draws, player_tiles, opp_tiles):
    if player_draws == 0:
        return [0, 0, 0, 0, 1, 0]

    player_tsumo_chance = player_tiles / wall
    opp_ron_chance = opp_tiles / wall
    advance_chance = 1 - player_tsumo_chance - opp_ron_chance

    action_matrix = [player_tsumo_chance, 0, opp_ron_chance, 0, 0, 0]

    advance_matrix = solve_shoubu_opp_draw(wall - 1, player_draws - 1, opp_draws, player_tiles, opp_tiles)
    advance_matrix = [advance_chance * x for x in advance_matrix]

    return list(map(add, action_matrix, advance_matrix))

def solve_shoubu_opp_draw(wall, player_draws, opp_draws, player_tiles, opp_tiles):
    if opp_draws == 0:
        return [0, 0, 0, 0, 1, 0]

    opp_tsumo_chance = opp_tiles / wall
    player_ron_chance = player_tiles / wall
    advance_chance = 1 - player_ron_chance - opp_tsumo_chance

    action_matrix = [0, player_ron_chance, 0, opp_tsumo_chance, 0, 0]

    advance_matrix = solve_shoubu_player_draw(wall - 1, player_draws, opp_draws - 1, player_tiles, opp_tiles)
    advance_matrix = [advance_chance * x for x in advance_matrix]

    return list(map(add, action_matrix, advance_matrix))

wall = 24 + 13

player_draws = 6
opp_draws = 6

player_waits = 3
opp_waits = 2

shoubu_probability_matrix = solve_shoubu_opp_draw(wall, player_draws, opp_draws, player_waits, opp_waits)
fold_probability_matrix = solve_fold_opp_draw(wall, player_draws, opp_draws, opp_waits)

player_tsumo_result = [210, 340, 230, 220]
player_ron_result = [250, 340, 250, 160]
opp_tsumo_result = [210, 230, 230, 330]
opp_ron_result = [250, 170, 250, 330]
tenpai_result = [235, 265, 235, 255]
noten_result = [240, 240, 240, 260]

"""
player_tsumo_result = [210, 330, 230, 230]
player_ron_result = [250, 330, 250, 170]
opp_tsumo_result = [210, 230, 230, 330]
opp_ron_result = [250, 170, 250, 330]
tenpai_result = [235, 265, 235, 265]
noten_result = [240, 240, 240, 270]
"""

payoff_matrix = [90, 45, 0, -135]
result_matrix = [
    player_tsumo_result,
    player_ron_result,
    opp_ron_result,
    opp_tsumo_result,
    tenpai_result,
    noten_result
]

kyoku = 1

result_payoff_matrix = [
    calc_placement_ev(
        player_seat=1,
        kyoku=kyoku,
        scores=result,
        payoff_matrix=payoff_matrix
    ) for result in result_matrix
]

# print(shoubu_probability_matrix)
# print(fold_probability_matrix)
# print(result_payoff_matrix)

deal_in_prob = 0

shoubu_ev_matrix = list(map(mul, shoubu_probability_matrix, result_payoff_matrix))
shoubu_ev = sum(shoubu_ev_matrix)

fold_ev_matrix = list(map(mul, fold_probability_matrix, result_payoff_matrix))
fold_ev = sum(fold_ev_matrix)

deal_in_ev = result_payoff_matrix[2]

print(f"Riichi EV: {deal_in_ev * deal_in_prob + shoubu_ev * (1 - deal_in_prob)}")
print(f"Shoubu EV: {shoubu_ev}")
print(f"Deal-in EV: {deal_in_ev}")
print(f"Fold EV: {fold_ev}")

threshold = (fold_ev - shoubu_ev) / (deal_in_ev - shoubu_ev)
print(f"Threshold: {threshold}")
print("")

tenpai_result = [235, 265, 235, 265]
noten_result = [240, 240, 240, 270]
deal_in_result = [250, 170, 250, 330]

tenpai_ev = calc_placement_ev(player_seat=1, kyoku=kyoku, scores=tenpai_result, payoff_matrix=payoff_matrix)
noten_ev = calc_placement_ev(player_seat=1, kyoku=kyoku, scores=noten_result, payoff_matrix=payoff_matrix)
deal_in_ev = calc_placement_ev(player_seat=1, kyoku=kyoku, scores=deal_in_result, payoff_matrix=payoff_matrix)

print(f"Tenpai EV: {tenpai_ev}")
print(f"Noten EV: {noten_ev}")
print(f"Deal-in EV: {deal_in_ev}")

print(f"Threshold: {(noten_ev - tenpai_ev) / (deal_in_ev - tenpai_ev)}")

agari = Game_Agari(actor=1, target=2, han=4, fu=30)
new_scores = agari.apply(0, [250, 250, 250, 250])

print(new_scores)