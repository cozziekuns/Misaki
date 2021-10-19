from operator import add, mul

from game import Game_Agari
from placement import Calculator_PlacementEv

#=============================================================================
# ** Solver_Shoubu
#=============================================================================

class Solver_Shoubu:

    def __init__(
        self,
        round_info,
        player_seat,
        opp_seat,
        payoff_matrix,
        use_uma=False,
    ):
        self.placement_ev_calculator = Calculator_PlacementEv(use_uma=use_uma)

        self.round_info = round_info

        self.player_seat = player_seat
        self.opp_seat = opp_seat

        self.payoff_matrix = payoff_matrix

        self.shoubu_matrix = None
        self.fold_matrix = None
        self.result_matrix = None
        self.result_odds_matrix = None
        self.result_payoff_matrix = None

    def get_next_kyoku(self, i):
        if self.round_info.kyoku == 7:
            return self.get_next_kyoku_all_last(i)

        if (
            (i in [0, 1, 4] and self.player_seat == self.round_info.kyoku % 4)
            or (i in [2, 3, 4, 5] and self.opp_seat == self.round_info.kyoku % 4)
        ):
            return self.round_info.kyoku
        else:
            return self.round_info.kyoku + 1

    def get_next_kyoku_all_last(self, i):
        if (
            (i in [0, 1, 4] and self.player_seat == 3) 
            or (i in [2, 3, 4, 5] and self.opp_seat == 3)
        ):
            oya_score = self.result_matrix[i][3]

            if (
                oya_score >= 300
                and max(self.result_matrix[i]) == oya_score
                and self.result_matrix[i].count(oya_score) == 1
            ):
                return -1
            else:
                return self.round_info.kyoku
        else:
            if max(self.result_matrix[i]) >= 300:
                return -1
            else:
                return self.round_info.kyoku + 1

    def next_kyoku_matrix(self):
        return [self.get_next_kyoku(i) for i in range(0, 6)]

    def push_matrix(self, tenpai_deal_in):
        push_matrix = list(map(lambda x: (1 - tenpai_deal_in) * x, self.shoubu_matrix))
        push_matrix[2] += tenpai_deal_in

        return push_matrix

    def shoubu_ev(self):
        shoubu_ev_matrix = list(map(mul, self.shoubu_matrix, self.result_payoff_matrix))

        return sum(shoubu_ev_matrix)

    def push_ev(self, tenpai_deal_in):
        a = self.shoubu_ev()
        b = self.deal_in_ev()

        return b * tenpai_deal_in + a * (1 - tenpai_deal_in)

    def fold_ev(self):
        fold_ev_matrix = list(map(mul, self.fold_matrix, self.result_payoff_matrix))

        return sum(fold_ev_matrix)

    def deal_in_ev(self):
        return self.result_payoff_matrix[2]

    def threshold(self):
        a = self.shoubu_ev()
        b = self.deal_in_ev()
        c = self.fold_ev()

        return (c - a) / (b - a)

    def tenpai_seats(self, player_tenpai=True):
        result = [0, 0, 0, 0]

        if player_tenpai:
            result[self.player_seat] = 1

        result[self.opp_seat] = 1

        return result

    def refresh_result_matrix(self, agari_value_matrix):
        self.result_matrix = []

        actor_target_pairs = [
            (self.player_seat, self.player_seat),
            (self.player_seat, self.opp_seat),
            (self.opp_seat, self.player_seat),
            (self.opp_seat, self.opp_seat),
        ]

        for i in range(0, 4):
            agari_result = Game_Agari(
                actor=actor_target_pairs[i][0],
                target=actor_target_pairs[i][1],
                han=agari_value_matrix[i][0],
                fu=agari_value_matrix[i][1],
            ).resolve(self.round_info)

            self.result_matrix.append(agari_result)

        self.result_matrix.append(
            self.calc_tenpai_result(
                self.round_info,
                self.tenpai_seats(player_tenpai=True),
            ),
        )

        self.result_matrix.append(
            self.calc_tenpai_result(
                self.round_info,
                self.tenpai_seats(player_tenpai=False),
            ),
        )

    def solve(self, live_wall, player_waits, opp_waits):
        wall = live_wall + 13

        opp_draws = (live_wall + (self.opp_seat - self.player_seat) % 4) // 4
        player_draws = live_wall // 4

        self.shoubu_matrix = self.solve_shoubu_opp_draw(
            wall,
            player_draws,
            opp_draws,
            player_waits,
            opp_waits,
        )

        self.fold_matrix = self.solve_fold_opp_draw(
            wall,
            player_draws,
            opp_draws,
            opp_waits,
        )

        self.result_payoff_matrix = []
        self.result_odds_matrix = []

        kyoku_matrix = self.next_kyoku_matrix()

        for i in range(0, 6):
            self.placement_ev_calculator.refresh(
                kyoku=kyoku_matrix[i],
                scores=self.result_matrix[i],
                payoff_matrix=self.payoff_matrix,
            )

            self.result_odds_matrix.append(self.placement_ev_calculator.prob_matrix)

            self.result_payoff_matrix.append(
                self.placement_ev_calculator.calc_placement_ev(self.player_seat)
            )

    def solve_fold_player_draw(self, wall, player_draws, opp_draws, opp_waits):
        if player_draws == 0:
            return [0, 0, 0, 0, 0, 1]

        player_block_chance = opp_waits / wall
        advance_chance = 1 - player_block_chance

        block_matrix = self.solve_fold_opp_draw(
            wall - 1,
            player_draws - 1,
            opp_draws,
            opp_waits - 1,
        )
        block_matrix = [player_block_chance * x for x in block_matrix]

        advance_matrix = self.solve_fold_opp_draw(
            wall - 1,
            player_draws - 1,
            opp_draws,
            opp_waits,
        )
        advance_matrix = [advance_chance * x for x in advance_matrix]

        return list(map(add, block_matrix, advance_matrix))

    def solve_fold_opp_draw(self, wall, player_draws, opp_draws, opp_waits):
        if opp_draws == 0:
            return [0, 0, 0, 0, 0, 1]

        opp_tsumo_chance = opp_waits / wall
        advance_chance = 1 - opp_tsumo_chance

        action_matrix = [0, 0, 0, opp_tsumo_chance, 0, 0]

        advance_matrix = self.solve_fold_player_draw(
            wall - 1,
            player_draws,
            opp_draws - 1,
            opp_waits,
        )
        advance_matrix = [advance_chance * x for x in advance_matrix]

        return list(map(add, action_matrix, advance_matrix))

    def solve_shoubu_player_draw(self, wall, player_draws, opp_draws, player_waits, opp_waits):
        if player_draws == 0:
            return [0, 0, 0, 0, 1, 0]

        player_tsumo_chance = player_waits / wall
        opp_ron_chance = opp_waits / wall
        advance_chance = 1 - player_tsumo_chance - opp_ron_chance

        action_matrix = [player_tsumo_chance, 0, opp_ron_chance, 0, 0, 0]

        advance_matrix = self.solve_shoubu_opp_draw(
            wall - 1,
            player_draws - 1,
            opp_draws,
            player_waits,
            opp_waits,
        )

        advance_matrix = [advance_chance * x for x in advance_matrix]

        return list(map(add, action_matrix, advance_matrix))

    def solve_shoubu_opp_draw(self, wall, player_draws, opp_draws, player_waits, opp_waits):
        if opp_draws == 0:
            return [0, 0, 0, 0, 1, 0]

        opp_tsumo_chance = opp_waits / wall
        player_ron_chance = player_waits / wall
        advance_chance = 1 - player_ron_chance - opp_tsumo_chance

        action_matrix = [0, player_ron_chance, 0, opp_tsumo_chance, 0, 0]

        advance_matrix = self.solve_shoubu_player_draw(
            wall - 1,
            player_draws,
            opp_draws - 1,
            player_waits,
            opp_waits,
        )

        advance_matrix = [advance_chance * x for x in advance_matrix]

        return list(map(add, action_matrix, advance_matrix))

    def calc_tenpai_result(self, round_info, tenpai_matrix):
        result = round_info.scores[:]
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
