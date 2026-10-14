"""Readable single-feature PFI trace for the interactive course lesson.

The caller supplies an already fitted model and the recorded row permutations.
This function changes no model parameters and restores the original matrix for
 every repeat. It uses the probability of the positive class, as in srag_62_pfi.
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import brier_score_loss


def trace_feature(model, x_eval, y_eval, feature, orders):
    """Return the original error and every perturbed error for one input."""
    original = x_eval.copy(deep=True)
    p_original = np.asarray(model.predict_proba(x_eval)[:, 1], dtype=np.float64)
    e_original = float(brier_score_loss(y_eval, p_original))
    errors = []
    for order in orders:
        if not np.array_equal(np.sort(order), np.arange(len(x_eval))):
            raise ValueError("Each order must permute all evaluation rows.")
        x_permuted = x_eval.copy()
        x_permuted[feature] = x_eval[feature].iloc[order].set_axis(x_eval.index)
        assert x_permuted[feature].dtype == x_eval[feature].dtype
        assert all(
            x_permuted[col].equals(x_eval[col]) for col in x_eval if col != feature
        )
        p_permuted = np.asarray(model.predict_proba(x_permuted)[:, 1], dtype=np.float64)
        errors.append(float(brier_score_loss(y_eval, p_permuted)))
    assert x_eval.equals(original)
    return e_original, np.asarray(errors)
