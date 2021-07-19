import math

#==============================================================================
# ** Game_Agari
#==============================================================================

class Game_Agari:

    def __init__(self, actor, target, han, fu):
        self.actor = actor
        self.target = target
        self.han = han
        self.fu = fu

    def apply(self, kyoku, score, riichi_sticks, homba):
        oya_index = kyoku % 4

        if self.actor == self.target:
            result = self.apply_tsumo(kyoku, score, self.actor == oya_index)

            # Apply homba
            for i in range(0, 4):
                result[i] = result[i] + 3 * homba if self.actor == i else result[i] - 1 * homba
        else:
            result = self.apply_ron(kyoku, score, self.actor == oya_index)

            # Apply homba
            result[self.actor] += 3 * homba
            result[self.target] -= 3 * homba

        # Apply riichi sticks
        result[self.actor] += riichi_sticks * 10
        return result

    def apply_tsumo(self, kyoku, score, oya=False):
        result = score[:]
        oya_index = kyoku % 4

        ko_diff = self.calc_ko_tsumo_payment()
        oya_diff = diff = self.calc_oya_tsumo_payment()

        if oya:
            for i in range(0, 4):
                if i == self.actor:
                    result[i] += oya_diff * 3
                else:
                    result[i] -= oya_diff
        else:
            for i in range(0, 4):
                if i == self.actor:
                    result[i] += 2 * ko_diff + oya_diff
                elif i == oya_index:
                    result[i] -= oya_diff
                else:
                    result[i] -= ko_diff

        return result

    def apply_ron(self, kyoku, score, oya=False):
        result = score[:]

        diff = self.calc_oya_ron_payment() if oya else self.calc_ko_ron_payment()

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
