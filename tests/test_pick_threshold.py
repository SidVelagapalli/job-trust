"""Tests for pick_threshold in src/thresholds.py.

Rule (2026-10-31): among thresholds whose precision is >= min_precision, return the one
with the highest recall. Ties -> the lowest threshold. None qualify -> ValueError.
A posting is flagged when its probability is >= the threshold; the candidate thresholds are the
probabilities themselves.
"""

import numpy as np
import pandas as pd
import pytest

from src.thresholds import pick_threshold

# t=0.8 -> precision 3/3, recall 3/4.  t=0.6 -> precision 4/5 = 0.80 exactly, recall 4/4.
PROBS = [0.95, 0.9, 0.8, 0.7, 0.6, 0.3]
Y = [1, 1, 1, 0, 1, 0]


def test_highest_recall_with_precision_at_least_min():
    assert pick_threshold(PROBS, Y, min_precision=0.80) == 0.6   # 0.80 exactly counts


def test_stricter_min_precision_gives_higher_threshold():
    assert pick_threshold(PROBS, Y, min_precision=0.81) == 0.8


def test_default_min_precision_is_0_80():
    assert pick_threshold(PROBS, Y) == 0.6


def test_tie_on_recall_returns_lowest_threshold():
    # 0.96 and 0.5 both catch all 4 scams with precision >= 0.80 (1.0 and 0.80).
    probs = [0.99, 0.98, 0.97, 0.96, 0.5, 0.4]
    y = [1, 1, 1, 1, 0, 0]
    assert pick_threshold(probs, y, min_precision=0.80) == 0.5


def test_no_threshold_reaches_min_precision_raises():
    with pytest.raises(ValueError):
        pick_threshold([0.9, 0.8], [0, 1], min_precision=0.80)   # precision 0.0 and 0.5


def test_repeated_probabilities_are_one_threshold():
    # Both 0.7s are flagged together: at t=0.7 precision is 2/3, so the answer is 0.9, not 0.7.
    assert pick_threshold([0.9, 0.7, 0.7, 0.2], [1, 1, 0, 0]) == 0.9


def test_works_with_numpy_and_shuffled_pandas_index():
    # In the notebook y_train is a pandas Series whose index is shuffled by train_test_split.
    y = pd.Series(Y, index=[17, 3, 250, 9, 41, 2])
    assert pick_threshold(np.array(PROBS), y, min_precision=0.80) == 0.6
