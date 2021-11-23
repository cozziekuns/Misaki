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
    
    def __init__(self, use_uma=False):
        self.models = [
            lgb.Booster(model_file=f"./static/models/placement/full_{i}.model")
            for i in range(0, 8)
        ]

        self.kyoku = None
        self.homba = None
        self.riibou = None

        self.scores = None

        self.payoff_matrix = None
        self.prob_matrix = None
        
        self.use_uma = use_uma

    def final_placements(self):
        totals = np.zeros((4, 4))
        
        for i, v in enumerate(sorted(list(enumerate(self.scores)), key=lambda x: -x[1])):
            totals[v[0]][i] = 1

        return totals

    def refresh(self, kyoku, homba, riibou, scores, payoff_matrix):
        self.kyoku = kyoku
        self.homba = homba
        self.riibou = riibou

        self.scores = scores

        self.prob_matrix = self.calc_prob_matrix()
        self.payoff_matrix = payoff_matrix

    def calc_prob_matrix(self):
        if self.kyoku < 0:
            return self.final_placements()

        input_vector = self.scores + [self.homba, self.riibou]
        
        model = self.models[min(self.kyoku, 7)]
        probs = model.predict(np.array([input_vector]))[0]

        totals = np.zeros((4, 4))

        for i in range(0, 24):
            for j in range(0, 4):
                totals[j][self.PERMUTATIONS[i][j]] += probs[i]

        return totals

    def calc_placement_ev(self, player_seat):
        if self.prob_matrix is None:
            raise Exception("Prob Matrix has not been set.")

        result = np.dot(self.prob_matrix[player_seat], self.payoff_matrix)

        if self.use_uma:
            result += self.scores[player_seat] / 10 - 25

        return result
