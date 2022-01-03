from operator import sub

import numpy as np

from flask import Flask
from flask import render_template
from flask import request
from flask import url_for

from deal_in import get_deal_in_probs
from game import Game_RoundInfo
from placement import Calculator_PlacementEv
from solver import Solver_DealIn
from solver import Solver_Fold
from solver import Solver_Shoubu

WIND_NAMES = ['east', 'south', 'west', 'north']
SEAT_NAMES = ['East', 'South', 'West', 'North']
PLACEMENT_NAMES = ['first', 'second', 'third', 'fourth']

SHOUBU_SECTION_TITLES = [
    'Player Tsumo Result',
    'Player Ron Result',
    'Opponent Ron Result',
    'Opponent Tsumo Result',
    'Player Tenpai Ryuukyoku Result',
    'Player Noten Ryuukyoku Result',
]

#==============================================================================
# ** Utility
#==============================================================================

def format_kyoku(kyoku):
    if kyoku < 0:
        return 'Game End'

    return SEAT_NAMES[kyoku // 4] + ' ' + str(kyoku % 4 + 1)

def get_base_scores_from_request(request):
    return [int(request.args[wind + '_player_score']) for wind in WIND_NAMES]

def get_shoubu_base_round_info(request):
    kyoku = int(request.args['kyoku'])
    riichi_sticks = int(request.args['riichi_sticks'])
    homba = int(request.args['homba'])
    scores = get_base_scores_from_request(request)   

    real_scores = [0, 0, 0, 0]

    for seat in range(0, 4):
        real_index = (seat + (kyoku % 4)) % 4
        real_scores[real_index] = scores[seat]

    return Game_RoundInfo(kyoku, homba, riichi_sticks, real_scores)

def get_shoubu_round_info(request, player_seat):
    round_info = get_shoubu_base_round_info(request)

    if request.args.get('declare_riichi') == 'riichi':
        round_info.riichi_sticks += 1
        round_info.scores[player_seat] -= 10

    return round_info

def get_shoubu_agari_value_matrix(request):
    player_tsumo_han = int(request.args['player_tsumo_han'])
    player_tsumo_fu = int(request.args['player_tsumo_fu'])
    player_ron_han = int(request.args['player_ron_han'])
    player_ron_fu = int(request.args['player_ron_fu'])

    opp_tsumo_han = int(request.args['opp_tsumo_han'])
    opp_tsumo_fu = int(request.args['opp_tsumo_fu'])
    opp_ron_han = int(request.args['opp_ron_han'])
    opp_ron_fu = int(request.args['opp_ron_fu'])

    return [
        (player_tsumo_han, player_tsumo_fu),
        (player_ron_han, player_ron_fu),
        (opp_ron_han, opp_ron_fu),
        (opp_tsumo_han, opp_tsumo_fu),
    ]

def get_shoubu_calculator(request):
    payoff_matrix = [int(request.args[name + '_place_bonus']) for name in PLACEMENT_NAMES]
    use_uma = request.args['bonus_type'] == 'uma_bonus'
    
    return Calculator_PlacementEv(payoff_matrix, use_uma=use_uma)

#==============================================================================
# ** Main Application
#==============================================================================

app = Flask(__name__)

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/placement")
def placement():
    return render_template('placement.html')

@app.route("/deal_in")
def deal_in():
    return render_template('deal_in.html')

@app.route("/calc_deal_in")
def calc_deal_in():
    dora_string = request.args['dora']
    discard_string = request.args['discards']
    
    deal_in_prob_strings = [
        f'{prob:.1%}'
        for prob in get_deal_in_probs(dora_string, discard_string)
    ]

    return render_template(
        'deal_in_probs.html',
        dora_string=dora_string,
        discard_string=discard_string,
        deal_in_probs=deal_in_prob_strings,
    )

@app.route("/shoubu")
def shoubu():
    return render_template('shoubu.html')

@app.route("/shoubu_ev")
def shoubu_ev(): 
    base_round_info = get_shoubu_base_round_info(request)
    
    tenpai_deal_in = int(request.args['tenpai_deal_in']) / 100
    live_wall = int(request.args['tiles_live_wall'])

    player_seat = int(request.args['player_seat'])
    opp_seat = int(request.args['opp_seat'])

    real_player_seat = (player_seat + (base_round_info.kyoku % 4)) % 4
    real_opp_seat = (opp_seat + (base_round_info.kyoku % 4)) % 4

    player_waits = int(request.args['player_waits'])
    opp_waits = int(request.args['opp_waits'])

    shoubu_round_info = get_shoubu_round_info(request, real_player_seat)

    agari_value_matrix = get_shoubu_agari_value_matrix(request)
    
    calculator = get_shoubu_calculator(request)

    shoubu_solver = Solver_Shoubu(calculator, shoubu_round_info, real_player_seat, real_opp_seat, agari_value_matrix)
    shoubu_solver.solve(live_wall, player_waits, opp_waits)

    fold_solver = Solver_Fold(calculator, base_round_info, real_player_seat, real_opp_seat, agari_value_matrix)
    fold_solver.solve(live_wall, opp_waits)

    deal_in_solver = Solver_DealIn(calculator, base_round_info, real_player_seat, real_opp_seat, agari_value_matrix)
    deal_in_solver.solve()

    push_matrix = list(map(lambda outcome_chance: (1 - tenpai_deal_in) * outcome_chance, shoubu_solver.outcome_matrix))
    push_matrix[2] += tenpai_deal_in

    push_ev = tenpai_deal_in * deal_in_solver.ev() + (1 - tenpai_deal_in) * shoubu_solver.ev()
    threshold = (fold_solver.ev() - shoubu_solver.ev()) / (deal_in_solver.ev() - shoubu_solver.ev())

    calculator.refresh(base_round_info)

    curr_odds_matrix = calculator.prob_matrix[real_player_seat]
    curr_placement_ev = calculator.calc_placement_ev(real_player_seat)

    formatted_result_matrix = []
    formatted_result_diff_matrix = []

    for i in range(0, 6):
        result = [score for score in shoubu_solver.result_matrix[i]]
        result_diff = list(map(sub, result, shoubu_round_info.scores))

        final_matrix = [0, 0, 0, 0]
        final_diff_matrix = [0, 0, 0, 0]

        for j in range(0, 4):
            new_index = (j - (shoubu_solver.get_next_kyoku(i) % 4)) % 4

            final_matrix[new_index] = result[j] * 100
            final_diff_matrix[new_index] = f"+{result_diff[j] * 100}" if result_diff[j] > 0 else str(result_diff[j] * 100)

        formatted_result_matrix.append(final_matrix)
        formatted_result_diff_matrix.append(final_diff_matrix)

    formatted_result_payoff_matrix = [f"{result:.4f}" for result in shoubu_solver.outcome_placement_ev_matrix]
    formatted_result_odds_matrix = [
        [[f"{prob:.2%}" for prob in placements] for placements in matrix] 
        for matrix in shoubu_solver.outcome_placement_odds_matrix
    ]

    return render_template(
        'shoubu_ev.html',
        section_titles=SHOUBU_SECTION_TITLES,
        real_player_seat=real_player_seat,
        kyoku=format_kyoku(base_round_info.kyoku),
        riichi_sticks=base_round_info.riichi_sticks,
        homba=base_round_info.homba,
        curr_scores=get_base_scores_from_request(request),
        formatted_player_seat=SEAT_NAMES[player_seat],
        formatted_opp_seat=SEAT_NAMES[opp_seat],
        payoff_matrix=calculator.payoff_matrix,
        curr_odds_matrix=[f"{prob:.2%}"for prob in curr_odds_matrix],
        curr_placement_ev=f"{curr_placement_ev:.4f}",
        next_kyoku_matrix=[format_kyoku(shoubu_solver.get_next_kyoku(i)) for i in range(0, 6)],
        result_matrix=formatted_result_matrix,
        result_diff_matrix=formatted_result_diff_matrix,
        result_odds_matrix=formatted_result_odds_matrix,
        result_payoff_matrix=formatted_result_payoff_matrix,
        shoubu_odds=[f"{prob:.2%}" for prob in shoubu_solver.outcome_matrix],
        fold_odds=[f"{prob:.2%}" for prob in fold_solver.outcome_matrix],
        push_ev=f"{push_ev:.4f}",
        shoubu_ev=f"{shoubu_solver.ev():.4f}",
        deal_in_ev=f"{deal_in_solver.ev():.4f}",
        fold_ev=f"{fold_solver.ev():.4f}",
        threshold=f"{threshold:.2%}",
        tenpai_deal_in=int(tenpai_deal_in * 100),
    )

@app.route("/placement_ev")
def placement_ev():
    round_info = get_shoubu_base_round_info(request)
    
    player_seat = int(request.args['player_seat'])
    new_player_seat = (player_seat + (round_info.kyoku % 4)) % 4

    payoff_matrix = [int(request.args[name + '_place_bonus']) for name in PLACEMENT_NAMES]

    calculator = Calculator_PlacementEv(
        payoff_matrix,
        use_uma=request.args['bonus_type'] == 'uma_bonus',
    )

    calculator.refresh(round_info)
    placement_ev = calculator.calc_placement_ev(new_player_seat)

    formatted_matrix = list(
        map(
            lambda placements: list(map(lambda prob: f"{prob:.2%}", placements)),
            calculator.prob_matrix,
        )
    )

    # Have to convert the winds back to the original winds.
    final_matrix = [None] * 4

    for i in range(0, 4):
        new_index = (i - (round_info.kyoku % 4)) % 4
        final_matrix[new_index] = formatted_matrix[i]

    return render_template(
        'placement_ev.html',
        kyoku=format_kyoku(round_info.kyoku),
        scores=get_base_scores_from_request(request),
        payoff=payoff_matrix,
        player_index=player_seat,
        ev=f"{placement_ev:.4f}",
        matrix=final_matrix,
    )

if __name__ == '__main__':
    app.run(threaded=True, port=5000)
