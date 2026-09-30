"""Similarity-weighted k-nearest-neighbours, RouteLLM's non-parametric router,
as an ablation for the logistic models."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np


def oof_probabilities(X: np.ndarray, y: np.ndarray, fold_of: Sequence[int], k: int = 20) -> np.ndarray:
    fold_of = np.asarray(fold_of)
    unit = X / np.linalg.norm(X, axis=1, keepdims=True)
    p = np.zeros(len(y))
    for f in sorted(set(fold_of.tolist())):
        test, train = fold_of == f, fold_of != f
        sims = unit[test] @ unit[train].T
        kk = min(k, int(train.sum()))
        idx = np.argsort(-sims, axis=1)[:, :kk]
        w = np.clip(np.take_along_axis(sims, idx, axis=1), 1e-9, None)
        p[test] = (w * y[train][idx]).sum(axis=1) / w.sum(axis=1)
    return p
