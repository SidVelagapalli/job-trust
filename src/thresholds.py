"""Pick the decision threshold for the scam model.

Rule (2026-10-31): among thresholds whose precision is >= min_precision, return the one
with the highest recall. Ties -> the lowest threshold (it catches at least as many scams).
None qualify -> ValueError (fail loudly instead of returning a bad threshold).

A posting is flagged when its probability is >= the threshold. The candidate thresholds are the
distinct probabilities themselves: any cut-off between two of them flags the same postings.
Use this on cross-validated TRAINING predictions only, never on the test set.
"""

import numpy as np


def pick_threshold(probs, y, min_precision: float = 0.80) -> float:
    # np.asarray drops any pandas index, so values line up by position, not by index label.
    probs = np.asarray(probs, dtype=float)
    y = np.asarray(y).astype(int)
    if probs.shape != y.shape:
        raise ValueError(f"probs and y have different shapes: {probs.shape} vs {y.shape}")

    total_scams = y.sum()
    if total_scams == 0:
        raise ValueError("y has no scams (no 1s), so recall is undefined")

    best_t, best_recall = None, -1.0
    # np.unique sorts lowest first and removes repeats. Going lowest first and only replacing
    # on a strictly higher recall means a tie keeps the lower threshold.
    for t in np.unique(probs):
        flagged = probs >= t
        caught = int((flagged & (y == 1)).sum())
        precision = caught / int(flagged.sum())  # never 0 flagged: t is one of the probs
        recall = caught / total_scams
        if precision >= min_precision and recall > best_recall:
            best_t, best_recall = float(t), recall

    if best_t is None:
        raise ValueError(f"no threshold reaches precision >= {min_precision}")
    return best_t
