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

def calc_tenpai_result(scores, tenpai_matrix):
    result = scores[:]
    players_tenpai = sum(tenpai_matrix)

    if players_tenpai % 4 == 0:
        return result

    for i in range(0, 4):
        if players_tenpai == 3:
            result[i] += (10 if tenpai_matrix[i] == 1 else -30)
        elif players_tenpai == 2:
            result[i] += (15 if tenpai_matrix[i] == 1 else -15)
        else:
            result[i] += (30 if tenpai_matrix[i] == 1 else -10)

    return result

def calc_placement_ev(player_seat, kyoku, scores, payoff_matrix):
    prob_matrix = calc_prob_matrix(kyoku, scores)

    print(f"{[kyoku] + scores}")

    strings = ['1st: ', '2nd: ', '3rd: ', '4th: ']
    for i in range(0, 4):
        print(f"{strings[i]} {prob_matrix[player_seat][i]:.3%}")

    result = np.dot(prob_matrix[player_seat], payoff_matrix)

    print(f"Placement EV: {result}")
    print("")

    return result

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

"""
wall = 24 + 13

player_draws = 6
opp_draws = 6

player_waits = 2
opp_waits = 2
"""

wall = 43 + 13
player_draws = 10
opp_draws = 11

player_waits = 3
opp_waits = 3

riichi_sticks = 1
homba = 1

shoubu_probability_matrix = solve_shoubu_opp_draw(wall, player_draws, opp_draws, player_waits, opp_waits)
fold_probability_matrix = solve_fold_opp_draw(wall, player_draws, opp_draws, opp_waits)

kyoku = 4
curr_scores = [178, 425, 174, 213]

player_seat = 0
opp_seat = 1

tenpai_seats = [0, 0, 0, 0]
tenpai_seats[player_seat] = 1
tenpai_seats[opp_seat] = 1

noten_seats = [0, 0, 0, 0]
noten_seats[opp_seat] = 1

player_tsumo_result = Game_Agari(actor=player_seat, target=player_seat, han=1, fu=30).apply(kyoku, curr_scores, riichi_sticks, homba)
player_ron_result = Game_Agari(actor=player_seat, target=opp_seat, han=1, fu=30).apply(kyoku, curr_scores, riichi_sticks, homba)
opp_tsumo_result = Game_Agari(actor=opp_seat, target=opp_seat, han=4, fu=30).apply(kyoku, curr_scores, riichi_sticks, homba)
opp_ron_result = Game_Agari(actor=opp_seat, target=player_seat, han=3, fu=40).apply(kyoku, curr_scores, riichi_sticks, homba)

tenpai_result = calc_tenpai_result(curr_scores, tenpai_seats)
noten_result = calc_tenpai_result(curr_scores, noten_seats)

payoff_matrix = [90, 45, 0, -135]
result_matrix = [
    player_tsumo_result,
    player_ron_result,
    opp_ron_result,
    opp_tsumo_result,
    tenpai_result,
    noten_result
]

result_payoff_matrix = []

for i in range(0, len(result_matrix)):
    if i in [0, 1, 4] and player_seat == kyoku % 4:
        next_kyoku = kyoku
    elif i in [2, 3, 4, 5] and opp_seat == kyoku % 4:
        next_kyoku = kyoku
    else:
        next_kyoku = kyoku + 1

    result_payoff_matrix.append(
        calc_placement_ev(
            player_seat=player_seat,
            kyoku=next_kyoku,
            scores=result_matrix[i],
            payoff_matrix=payoff_matrix,
        )
    )

print(result_payoff_matrix)

# print(shoubu_probability_matrix)
# print(fold_probability_matrix)
# print(result_payoff_matrix)

deal_in_prob = 0

shoubu_ev_matrix = list(map(mul, shoubu_probability_matrix, result_payoff_matrix))
shoubu_ev = sum(shoubu_ev_matrix)

fold_ev_matrix = list(map(mul, fold_probability_matrix, result_payoff_matrix))
fold_ev = sum(fold_ev_matrix)

deal_in_ev = result_payoff_matrix[2]

print(f"Push EV: {deal_in_ev * deal_in_prob + shoubu_ev * (1 - deal_in_prob)}")
print(f"Shoubu EV: {shoubu_ev}")
print(f"Deal-in EV: {deal_in_ev}")
print(f"Fold EV: {fold_ev}")

print(shoubu_probability_matrix)
print(fold_probability_matrix)

threshold = (fold_ev - shoubu_ev) / (deal_in_ev - shoubu_ev)
print(f"Threshold: {threshold}")
print("")
