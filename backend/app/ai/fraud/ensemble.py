from __future__ import annotations

import numpy as np


def average_probabilities(probability_sets: list) -> np.ndarray:
    return np.mean(np.vstack(probability_sets), axis=0)

