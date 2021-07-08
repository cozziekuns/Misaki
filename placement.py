import numpy as np

from xgboost import XGBClassifier

#=============================================================================
# ** Calculator_PlacementEv
#=============================================================================

class Calculator_PlacementEv:

    PERMUTATIONS = [
        [0, 1, 2, 3], [0, 1, 3, 2], [0, 2, 1, 3], [0, 2, 3, 1], [0, 3, 1, 2], [0, 3, 2, 1],
        [1, 0, 2, 3], [1, 0, 3, 2], [1, 2, 0, 3], [1, 2, 3, 0], [1, 3, 0, 2], [1, 3, 2, 0],
        [2, 0, 1, 3], [2, 0, 3, 1], [2, 1, 0, 3], [2, 1, 3, 0], [2, 3, 0, 1], [2, 3, 1, 0],
        [3, 0, 1, 2], [3, 0, 2, 1], [3, 1, 0, 2], [3, 1, 2, 0], [3, 2, 0, 1], [3, 2, 1, 0],
    ]
    
    def __init__(self, payoff_matrix):
        self.model = XGBClassifier()
        self.model.load_model('./static/models/full.model')

        self.payoff_matrix = payoff_matrix

    def calc_placement_ev(self, player_seat, kyoku, scores):
        prob_matrix = self.calc_prob_matrix(kyoku, scores)

        return np.dot(prob_matrix[player_seat], self.payoff_matrix)

    def calc_prob_matrix(self, kyoku, scores):
        input_vector = [kyoku] + scores
        probs = self.model.predict_proba(np.array([input_vector]))[0]

        totals = [
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]

        for i in range(0, 24):
            for j in range(0, 4):
                totals[j][self.PERMUTATIONS[i][j]] += probs[i]

        return totals