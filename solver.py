from operator import add, mul

from game import Game_Agari
from game import Game_RoundInfo
from placement import Calculator_PlacementEv

#=============================================================================
# ** Solver_Base
#=============================================================================

class Solver_Base:
    
    def __init__(
        self,
        calculator,
        round_info,
        player_seat,
        opp_seat,
        agari_value_matrix,
    ):
        self.round_info = round_info
        self.player_seat = player_seat
        self.opp_seat = opp_seat
        
        self.agari_value_matrix = agari_value_matrix
        
        self.calculator = calculator
        
        self.outcome_matrix = []

        self.outcome_placement_ev_matrix = []
        self.outcome_placement_odds_matrix = []

        self.refresh_result_matrix()

    def ev(self):
        return sum(list(map(mul, self.outcome_matrix, self.outcome_placement_ev_matrix)))

    def is_oya(self, seat):
        return seat == self.round_info.kyoku % 4
    
    def is_outcome_renchan(self, outcome_index):
        if outcome_index in [0, 1, 4] and self.is_oya(self.player_seat):
            return True

        if outcome_index in [2, 3, 4, 5] and self.is_oya(self.opp_seat):
            return True

        return False
    
    def is_outcome_ryuukyoku(self, outcome_index):
        return outcome_index in [4, 5]

    def get_next_kyoku(self, outcome_index):
        if [score for score in self.result_matrix[outcome_index] if score < 0]:
            return -1
        
        if self.round_info.kyoku == 7:
            return self.get_next_kyoku_all_last(outcome_index)

        if self.is_outcome_renchan(outcome_index):
            return self.round_info.kyoku

        return self.round_info.kyoku + 1

    def get_next_kyoku_all_last(self, outcome_index):
        first_place_score = max(self.result_matrix[outcome_index])

        if self.is_outcome_renchan(outcome_index):    
            oya_score = self.result_matrix[outcome_index][3]

            if (
                oya_score >= 300
                and first_place_score == oya_score
                and self.result_matrix[outcome_index].count(oya_score) == 1
            ):
                return -1

            return self.round_info.kyoku
        elif first_place_score >= 300:
            return -1
        else:
            return self.round_info.kyoku + 1

    def get_next_bonus(self, outcome_index):
        if self.is_outcome_ryuukyoku(outcome_index):
            return [self.round_info.homba + 1, self.round_info.riichi_sticks]
        elif self.is_outcome_renchan(outcome_index):
            return [self.round_info.homba + 1, 0]
        else:
            return [0, 0]
 
    def get_next_round_info(self, outcome_index):
        homba, riichi_sticks = self.get_next_bonus(outcome_index)

        return Game_RoundInfo(
            self.get_next_kyoku(outcome_index),
            homba,
            riichi_sticks,
            self.result_matrix[outcome_index],
        )

    def tenpai_seats(self, player_tenpai=True):
        result = [0, 0, 0, 0]

        if player_tenpai:
            result[self.player_seat] = 1

        result[self.opp_seat] = 1

        return result

    def calc_tenpai_result(self, round_info, tenpai_seats):
        result = round_info.scores[:]
        players_tenpai = sum(tenpai_seats)

        if players_tenpai % 4 == 0:
            return result

        for i in range(0, 4):
            if players_tenpai == 3:
                result[i] += (10 if tenpai_seats[i] == 1 else -30)
            elif players_tenpai == 2:
                result[i] += (15 if tenpai_seats[i] == 1 else -15)
            else:
                result[i] += (30 if tenpai_seats[i] == 1 else -10)

        return result
 

#=============================================================================
# ** Solver_Shoubu
#=============================================================================

class Solver_Shoubu(Solver_Base):

    def refresh_result_matrix(self):
        actor_target_pairs = [
            (self.player_seat, self.player_seat),
            (self.player_seat, self.opp_seat),
            (self.opp_seat, self.player_seat),
            (self.opp_seat, self.opp_seat),
        ]

        self.result_matrix = [
            Game_Agari(
                actor=actor_target_pairs[i][0],
                target=actor_target_pairs[i][1],
                han=self.agari_value_matrix[i][0],
                fu=self.agari_value_matrix[i][1],
            ).resolve(self.round_info) for i in range(0, 4)
        ]

        self.result_matrix += [
            self.calc_tenpai_result(self.round_info, self.tenpai_seats(is_player_tenpai))
            for is_player_tenpai in [True, False]
        ]

    def solve(self, live_wall, player_waits, opp_waits):
        wall = live_wall + 13

        opp_draws = (live_wall + (self.opp_seat - self.player_seat) % 4) // 4
        player_draws = live_wall // 4

        self.outcome_matrix = self.solve_opp_draw(wall, player_draws, opp_draws, player_waits, opp_waits)

        self.outcome_placement_ev_matrix = []
        self.outcome_placement_odds_matrix = []

        for outcome_index in range(0, 6):
            self.calculator.refresh(self.get_next_round_info(outcome_index))

            self.outcome_placement_odds_matrix.append(self.calculator.prob_matrix)
            self.outcome_placement_ev_matrix.append(self.calculator.calc_placement_ev(self.player_seat))

    def solve_player_draw(self, wall, player_draws, opp_draws, player_waits, opp_waits):
        if player_draws == 0:
            return [0, 0, 0, 0, 1, 0]

        player_tsumo_chance = player_waits / wall
        opp_ron_chance = opp_waits / wall
        advance_chance = 1 - player_tsumo_chance - opp_ron_chance

        action_matrix = [player_tsumo_chance, 0, opp_ron_chance, 0, 0, 0]

        advance_matrix = self.solve_opp_draw(wall - 1, player_draws - 1, opp_draws, player_waits, opp_waits)
        advance_matrix = [advance_chance * outcome_ev for outcome_ev in advance_matrix]

        return list(map(add, action_matrix, advance_matrix))

    def solve_opp_draw(self, wall, player_draws, opp_draws, player_waits, opp_waits):
        if opp_draws == 0:
            return [0, 0, 0, 0, 1, 0]

        opp_tsumo_chance = opp_waits / wall
        player_ron_chance = player_waits / wall
        advance_chance = 1 - player_ron_chance - opp_tsumo_chance

        action_matrix = [0, player_ron_chance, 0, opp_tsumo_chance, 0, 0]
        
        advance_matrix = self.solve_player_draw(wall - 1, player_draws, opp_draws - 1, player_waits, opp_waits)
        advance_matrix = [advance_chance * outcome_ev for outcome_ev in advance_matrix]

        return list(map(add, action_matrix, advance_matrix))

#=============================================================================
# ** Solver_Fold
#=============================================================================

class Solver_Fold(Solver_Base):

    def refresh_result_matrix(self):
        opp_tsumo_result = Game_Agari(
            actor=self.opp_seat,
            target=self.opp_seat,
            han=self.agari_value_matrix[3][0],
            fu=self.agari_value_matrix[3][1],
        ).resolve(self.round_info)

        self.result_matrix = [0, 0, 0, opp_tsumo_result]

        self.result_matrix += [
            self.calc_tenpai_result(self.round_info, self.tenpai_seats(is_player_tenpai))
            for is_player_tenpai in [True, False]
        ]

    def solve(self, live_wall, opp_waits):
        wall = live_wall + 13

        opp_draws = (live_wall + (self.opp_seat - self.player_seat) % 4) // 4
        player_draws = live_wall // 4

        self.outcome_matrix = self.solve_opp_draw(wall, player_draws, opp_draws, opp_waits)

        self.outcome_placement_ev_matrix = []
        self.outcome_placement_odds_matrix = []

        for outcome_index in range(0, 6):
            if outcome_index in [3, 5]:
                self.calculator.refresh(self.get_next_round_info(outcome_index))

                self.outcome_placement_odds_matrix.append(self.calculator.prob_matrix)
                self.outcome_placement_ev_matrix.append(self.calculator.calc_placement_ev(self.player_seat))
            else:
                self.outcome_placement_odds_matrix.append([0, 0, 0, 0])
                self.outcome_placement_ev_matrix.append(0)

    def solve_player_draw(self, wall, player_draws, opp_draws, opp_waits):
        if player_draws == 0:
            return [0, 0, 0, 0, 0, 1]

        player_block_chance = opp_waits / wall
        advance_chance = 1 - player_block_chance

        block_matrix = self.solve_opp_draw(wall - 1, player_draws - 1, opp_draws, opp_waits - 1)
        block_matrix = [player_block_chance * outcome_chance for outcome_chance in block_matrix]

        advance_matrix = self.solve_opp_draw(wall - 1, player_draws - 1, opp_draws, opp_waits)
        advance_matrix = [advance_chance * outcome_chance for outcome_chance in advance_matrix]

        return list(map(add, block_matrix, advance_matrix))

    def solve_opp_draw(self, wall, player_draws, opp_draws, opp_waits):
        if opp_draws == 0:
            return [0, 0, 0, 0, 0, 1]

        opp_tsumo_chance = opp_waits / wall
        advance_chance = 1 - opp_tsumo_chance

        action_matrix = [0, 0, 0, opp_tsumo_chance, 0, 0]

        advance_matrix = self.solve_player_draw(wall - 1, player_draws, opp_draws - 1, opp_waits)
        advance_matrix = [advance_chance * x for x in advance_matrix]

        return list(map(add, action_matrix, advance_matrix))


#=============================================================================
# ** Solver_DealIn
#=============================================================================

class Solver_DealIn(Solver_Base):

    def refresh_result_matrix(self):
        deal_in_result = Game_Agari(
            actor=self.opp_seat,
            target=self.player_seat,
            han=self.agari_value_matrix[2][0],
            fu=self.agari_value_matrix[2][1],
        ).resolve(self.round_info)

        self.result_matrix = [0, 0, deal_in_result, 0, 0, 0]

    def solve(self):
        self.outcome_matrix = [0, 0, 1, 0, 0, 0]

        self.outcome_placement_ev_matrix = []
        self.outcome_placement_odds_matrix = []

        for outcome_index in range(0, 6):
            if outcome_index == 2:
                self.calculator.refresh(self.get_next_round_info(outcome_index))

                self.outcome_placement_odds_matrix.append(self.calculator.prob_matrix)
                self.outcome_placement_ev_matrix.append(self.calculator.calc_placement_ev(self.player_seat))
            else:
                self.outcome_placement_odds_matrix.append([0, 0, 0, 0])
                self.outcome_placement_ev_matrix.append(0)


#=============================================================================
# ** Solver_Agari
#=============================================================================

class Solver_Agari(Solver_Base):

    def is_tsumo(self):
        return self.player_seat == self.opp_seat

    def agari_index(self):
        return 0 if self.is_tsumo() else 1

    def refresh_result_matrix(self):
        agari_result = Game_Agari(
            actor=self.player_seat,
            target=self.opp_seat,
            han=self.agari_value_matrix[0][0] if self.is_tsumo() else self.agari_value_matrix[1][0],
            fu=self.agari_value_matrix[0][1] if self.is_tsumo() else self.agari_value_matrix[1][1],
        ).resolve(self.round_info)

        self.result_matrix = [None] * 6
        self.result_matrix[self.agari_index()] = agari_result

    def solve(self):
        self.outcome_matrix = [0] * 6
        self.outcome_matrix[self.agari_index()] = 1

        self.outcome_placement_ev_matrix = []
        self.outcome_placement_odds_matrix = []

        for outcome_index in range(0, 6):
            if outcome_index == self.agari_index():
                self.calculator.refresh(self.get_next_round_info(outcome_index))

                self.outcome_placement_odds_matrix.append(self.calculator.prob_matrix)
                self.outcome_placement_ev_matrix.append(self.calculator.calc_placement_ev(self.player_seat))
            else:
                self.outcome_placement_odds_matrix.append([0, 0, 0, 0])
                self.outcome_placement_ev_matrix.append(0)
