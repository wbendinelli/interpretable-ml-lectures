"""Readable single-feature PFI trace for the interactive course lesson.

The caller supplies an already fitted model and the recorded row permutations.
This wrapper calls the shared phase-70 kernel, changing no model parameters.
Every repeat starts from the original matrix. The positive-class convention
and float64 probabilities are the same as in srag_62_pfi.
"""

from __future__ import annotations

import srag_70_explain as E
from sklearn.metrics import brier_score_loss


def trace_feature(model, x_eval, y_eval, feature, orders, loss=brier_score_loss):
    """Return the original error and every perturbed error for one input."""
    return E.trace_pfi(model, x_eval, y_eval, feature, orders, loss)
