import numpy as np

import lightgbm as lgb

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
    
    def __init__(self):
        self.model = lgb.Booster(model_file='./static/models/placement.model')

        self.kyoku = None
        self.scores = None

        self.payoff_matrix = None
        self.prob_matrix = None

    def refresh(self, kyoku, scores, payoff_matrix):
        self.kyoku = kyoku
        self.scores = scores

        self.prob_matrix = self.calc_prob_matrix()
        self.payoff_matrix = payoff_matrix

    def calc_prob_matrix(self):
        input_vector = [self.kyoku] + self.scores
        probs = self.model.predict(np.array([input_vector]))[0]

        totals = np.zeros((4, 4))

        for i in range(0, 24):
            for j in range(0, 4):
                totals[j][self.PERMUTATIONS[i][j]] += probs[i]

        return totals

    def calc_placement_ev(self, player_seat):
        if self.prob_matrix is None:
            raise Exception("Prob Matrix has not been set.")

        return np.dot(self.prob_matrix[player_seat], self.payoff_matrix)
