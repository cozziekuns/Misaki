from operator import sub

import numpy as np

from flask import Flask
from flask import render_template
from flask import request
from flask import url_for

from game import Game_RoundInfo
from placement import Calculator_PlacementEv
from solver import Solver_Shoubu

#==============================================================================
# ** Utility
#==============================================================================

def format_kyoku(kyoku):
    return ['East', 'South'][kyoku // 4] + ' ' + str(kyoku % 4 + 1)

#==============================================================================
# ** Main Application
#==============================================================================

app = Flask(__name__)

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/shoubu")
def shoubu():
    return render_template('shoubu.html')

@app.route("/shoubu_ev")
def shoubu_ev():
    winds = ['east', 'south', 'west', 'north']
    placement_names = ['first', 'second', 'third', 'fourth']

    # --- Get Round Info ---

    kyoku = int(request.args['kyoku'])

    riichi_sticks = int(request.args['riichi_sticks'])
    homba = int(request.args['homba'])

    scores = [int(request.args[wind + '_player_score']) for wind in winds]
    
    real_scores = [0, 0, 0, 0]

    for i in range(0, 4):
        real_index = (i + (kyoku % 4)) % 4
        real_scores[real_index] = scores[i] // 100

    round_info = Game_RoundInfo(kyoku, riichi_sticks, homba, real_scores)

    # --- Get Shoubu Info ---

    tenpai_deal_in = int(request.args['tenpai_deal_in']) / 100
    live_wall = int(request.args['tiles_live_wall'])

    player_seat = int(request.args['player_seat'])
    opp_seat = int(request.args['opp_seat'])

    real_player_seat = (player_seat + (kyoku % 4)) % 4
    real_opp_seat = (opp_seat + (kyoku % 4)) % 4

    player_waits = int(request.args['player_waits'])
    opp_waits = int(request.args['opp_waits'])

    player_tsumo_han = int(request.args['player_tsumo_han'])
    player_tsumo_fu = int(request.args['player_tsumo_fu'])
    player_ron_han = int(request.args['player_ron_han'])
    player_ron_fu = int(request.args['player_ron_fu'])

    opp_tsumo_han = int(request.args['opp_tsumo_han'])
    opp_tsumo_fu = int(request.args['opp_tsumo_fu'])
    opp_ron_han = int(request.args['opp_ron_han'])
    opp_ron_fu = int(request.args['opp_ron_fu'])

    # --- Get Payoff Matrix ---

    payoff_matrix = [int(request.args[name + '_place_bonus']) for name in placement_names]

    solver = Solver_Shoubu(round_info, real_player_seat, real_opp_seat, payoff_matrix)
    solver.refresh_result_matrix(
        [
            (player_tsumo_han, player_tsumo_fu),
            (player_ron_han, player_ron_fu),
            (opp_tsumo_han, opp_tsumo_fu),
            (opp_ron_han, opp_ron_fu),
        ]
    )

    solver.solve(live_wall, player_waits, opp_waits)

    # --- Get Current Placement EV ---

    solver.placement_ev_calculator.refresh(
        kyoku=kyoku,
        scores=real_scores,
        payoff_matrix=payoff_matrix,
    )

    curr_odds_matrix = solver.placement_ev_calculator.prob_matrix[real_player_seat]
    curr_placement_ev = solver.placement_ev_calculator.calc_placement_ev(real_player_seat)

    # --- Format for frontend ---

    next_kyoku_matrix = solver.next_kyoku_matrix()

    formatted_result_matrix = []
    formatted_result_diff_matrix = []

    for i in range(0, 6):
        result = [score for score in solver.result_matrix[i]]
        result_diff = list(map(sub, result, real_scores))

        final_matrix = [0, 0, 0, 0]
        final_diff_matrix = [0, 0, 0, 0]

        for j in range(0, 4):
            new_index = (j - (next_kyoku_matrix[i] % 4)) % 4

            final_matrix[new_index] = result[j] * 100
            final_diff_matrix[new_index] = f"+{result_diff[j] * 100}" if result_diff[j] > 0 else str(result_diff[j] * 100)

        formatted_result_matrix.append(final_matrix)
        formatted_result_diff_matrix.append(final_diff_matrix)

    formatted_result_payoff_matrix = [f"{result:.4f}" for result in solver.result_payoff_matrix]
    formatted_result_odds_matrix = [
        [[f"{prob:.2%}" for prob in placements] for placements in matrix] 
        for matrix in solver.result_odds_matrix
    ]

    section_titles = [
        'Player Tsumo Result',
        'Player Ron Result',
        'Opponent Ron Result',
        'Opponent Tsumo Result',
        'Player Tenpai Ryuukyoku Result',
        'Player Noten Ryuukyoku Result'
    ]

    return render_template(
        'shoubu_ev.html',
        section_titles=section_titles,
        real_player_seat=real_player_seat,
        kyoku=format_kyoku(kyoku),
        riichi_sticks=riichi_sticks,
        homba=homba,
        curr_scores=scores,
        formatted_player_seat=['East', 'South', 'West', 'North'][player_seat],
        formatted_opp_seat=['East', 'South', 'West', 'North'][opp_seat],
        payoff_matrix=payoff_matrix,
        curr_odds_matrix=[f"{prob:.2%}"for prob in curr_odds_matrix],
        curr_placement_ev=f"{curr_placement_ev:.4f}",
        next_kyoku_matrix=[format_kyoku(kyoku) for kyoku in next_kyoku_matrix],
        result_matrix=formatted_result_matrix,
        result_diff_matrix=formatted_result_diff_matrix,
        result_odds_matrix=formatted_result_odds_matrix,
        result_payoff_matrix=formatted_result_payoff_matrix,
        shoubu_odds=[f"{prob:.2%}" for prob in solver.shoubu_matrix],
        fold_odds=[f"{prob:.2%}" for prob in solver.fold_matrix],
        push_ev=f"{solver.push_ev(tenpai_deal_in):.4f}",
        shoubu_ev=f"{solver.shoubu_ev():.4f}",
        deal_in_ev=formatted_result_payoff_matrix[2],
        fold_ev=f"{solver.fold_ev():.4f}",
        threshold=f"{solver.threshold():.2%}",
        tenpai_deal_in=int(tenpai_deal_in * 100),
    )

@app.route("/placement_ev")
def placement_ev():
    winds = ['east', 'south', 'west', 'north']
    placement_names = ['first', 'second', 'third', 'fourth']

    kyoku = int(request.args['kyoku'])
    player_seat = int(request.args['player_seat'])
    new_player_seat = (player_seat + (kyoku % 4)) % 4

    scores = [int(request.args[wind + '_player_score']) for wind in winds]
    real_scores = [0, 0, 0, 0]

    for i in range(0, 4):
        new_index = (i + (kyoku % 4)) % 4
        real_scores[new_index] = scores[i] // 100

    payoff_matrix = [int(request.args[name + '_place_bonus']) for name in placement_names]

    calculator = Calculator_PlacementEv()
    calculator.refresh(kyoku, real_scores, payoff_matrix)

    placement_ev = calculator.calc_placement_ev(new_player_seat)

    formatted_ev = f"{placement_ev:.4f}"
    formatted_matrix = list(
        map(
            lambda placements: list(map(lambda prob: f"{prob:.2%}", placements)),
            calculator.prob_matrix,
        )
    )

    # Have to convert the winds back to the original winds.
    final_matrix = [None] * 4

    for i in range(0, 4):
        new_index = (i - (kyoku % 4)) % 4
        final_matrix[new_index] = formatted_matrix[i]

    formatted_kyoku = ['East', 'South'][kyoku // 4] + ' ' + str(kyoku % 4 + 1)

    return render_template(
        'placement_ev.html',
        kyoku=formatted_kyoku,
        scores=scores,
        payoff=payoff_matrix,
        player_index=player_seat,
        ev=formatted_ev,
        matrix=final_matrix,
    )

if __name__ == '__main__':
    app.run(threaded=True, port=5000)