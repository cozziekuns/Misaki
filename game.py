import math

#==============================================================================
# ** Game_RoundInfo
#==============================================================================

class Game_RoundInfo:

    def __init__(self, kyoku, riichi_sticks, homba, scores):
        self.kyoku = kyoku

        self.riichi_sticks = riichi_sticks
        self.homba = homba

        self.scores = scores

    def oya_index(self):
        return self.kyoku % 4

#==============================================================================
# ** Game_Agari
#==============================================================================

class Game_Agari:

    def __init__(self, actor, target, han, fu):
        self.actor = actor
        self.target = target
        self.han = han
        self.fu = fu

    def resolve(self, round_info):
        if self.actor == self.target:
            result = self.apply_tsumo(round_info)

            # Apply homba
            for i in range(0, 4):
                if self.actor == i:
                    result[i] += 3 * round_info.homba 
                else:
                    result[i] -= round_info.homba
        else:
            result = self.apply_ron(round_info)

            # Apply homba
            result[self.actor] += 3 * round_info.homba
            result[self.target] -= 3 * round_info.homba

        # Apply riichi sticks
        result[self.actor] += round_info.riichi_sticks * 10

        return result

    def apply_tsumo(self, round_info):
        result = round_info.scores[:]

        ko_diff = self.calc_ko_tsumo_payment()
        oya_diff = diff = self.calc_oya_tsumo_payment()

        if self.actor == round_info.oya_index():
            for i in range(0, 4):
                if i == self.actor:
                    result[i] += oya_diff * 3
                else:
                    result[i] -= oya_diff
        else:
            for i in range(0, 4):
                if i == self.actor:
                    result[i] += 2 * ko_diff + oya_diff
                elif i == round_info.oya_index():
                    result[i] -= oya_diff
                else:
                    result[i] -= ko_diff

        return result

    def apply_ron(self, round_info):
        result = round_info.scores[:]
        diff = None

        if self.actor == round_info.oya_index():
            diff = self.calc_oya_ron_payment()
        else:
            diff = self.calc_ko_ron_payment()

        result[self.actor] += diff
        result[self.target] -= diff

        return result

    def round_up(self, points):
        return math.ceil(points / 100)

    def calc_basic_points(self):
        if self.han >= 13:
            return 8000
        elif self.han >= 11:
            return 6000
        elif self.han >= 8:
            return 4000
        elif self.han >= 6:
            return 3000
        else:
            return min(2000, math.ceil(self.fu * 2 ** (2 + self.han)))

    def calc_ko_tsumo_payment(self):
        return self.round_up(self.calc_basic_points())

    def calc_oya_tsumo_payment(self):
        return self.round_up(2 * self.calc_basic_points())

    def calc_ko_ron_payment(self):
        return self.round_up(4 * self.calc_basic_points())

    def calc_oya_ron_payment(self):
        return self.round_up(6 * self.calc_basic_points())
