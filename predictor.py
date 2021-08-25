import numpy as np
import lightgbm as lg
import os


def convert_back_to_legacy(data):
    return data[:, 1:21]


def featurize(data):
    """
    Extract features
        - first 20 features i-th discards from start
        - next 20 features are i-th discards from riichi
        - last 34 features count # of discards for each tile
    """
    res = np.empty((len(data), 20 + 20 + 34), dtype=np.uint8)
    res[:, :20] = data
    temp = data[:, ::-1]
    shifts = np.argmax(temp != 0, axis=1)
    shifts = np.arange(20)[np.newaxis, :] + shifts[:, np.newaxis]
    shifts[shifts >= 20] = 0
    res[:, 20:40] = temp[np.arange(data.shape[0])[:, np.newaxis], shifts]
    for k in range(34):
        res[:, 40 + k] = np.sum(temp == k + 1, axis=1)
    return res


CONV = np.array([0]+list(range(19, 28))+list(range(1, 19))+list(range(28, 32))+[34,32,33], dtype=np.uint8)


def shift(data):
    return CONV[data]


class Predictor:

    def __init__(self, model_dir):
        self.num_models = [lg.Booster(model_file=os.path.join(model_dir, f'{i+1}m.model')) for i in range(9)]
        self.wind_models = [lg.Booster(model_file=os.path.join(model_dir, f'{wind}.model'))
                            for wind in ['east', 'south', 'west', 'north']]
        self.haku_model = lg.Booster(model_file=os.path.join(model_dir, 'white.model'))

    def predict_batch(self, data):
        probs = np.empty((len(data), 34), dtype=np.float)
        data = convert_back_to_legacy(data)

        # 1m-9m, all winds, haku
        featurized = featurize(data)
        for k, model in enumerate(self.num_models):
            probs[:, k] = model.predict(featurized)
        for k, model in enumerate(self.wind_models):
            probs[:, k+27] = model.predict(featurized)
        probs[:, 31] = self.haku_model.predict(featurized)

        # 1p-9p, hatsu
        data = shift(data)
        featurized = featurize(data)
        for k, model in enumerate(self.num_models):
            probs[:, k+9] = model.predict(featurized)
        probs[:, 32] = self.haku_model.predict(featurized)

        # 1s-9s, chun
        data = shift(data)
        featurized = featurize(data)
        for k, model in enumerate(self.num_models):
            probs[:, k+18] = model.predict(featurized)
        probs[:, 33] = self.haku_model.predict(featurized)

        return probs

    def predict(self, data):
        prediction = self.predict_batch(np.array([data], dtype=np.uint8))
        return prediction[0]
