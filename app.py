import numpy as np

from flask import Flask
from flask import render_template
from flask import request
from flask import url_for

from xgboost import XGBClassifier

PERMUTATIONS = [
    [0, 1, 2, 3], [0, 1, 3, 2], [0, 2, 1, 3], [0, 2, 3, 1], [0, 3, 1, 2], [0, 3, 2, 1],
    [1, 0, 2, 3], [1, 0, 3, 2], [1, 2, 0, 3], [1, 2, 3, 0], [1, 3, 0, 2], [1, 3, 2, 0],
    [2, 0, 1, 3], [2, 0, 3, 1], [2, 1, 0, 3], [2, 1, 3, 0], [2, 3, 0, 1], [2, 3, 1, 0], 
    [3, 0, 1, 2], [3, 0, 2, 1], [3, 1, 0, 2], [3, 1, 2, 0], [3, 2, 0, 1], [3, 2, 1, 0],
]

def calculate_prob_matrix(kyoku, scores):
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

#==============================================================================
# ** Main Application
#==============================================================================

app = Flask(__name__)

@app.route("/")
def index():
    return render_template('index.html')

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

    prob_matrix = calculate_prob_matrix(kyoku, real_scores)
    placement_ev = np.dot(prob_matrix[new_player_seat], payoff_matrix)

    formatted_ev = f"{placement_ev:.4f}"
    formatted_matrix = list(
        map(
            lambda placements: list(map(lambda prob: f"{prob:.2%}", placements)),
            prob_matrix,
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