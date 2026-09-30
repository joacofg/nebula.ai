"""Cross-validation grouped by prompt.

A prompt and its translation carry the same prompt_id; letting one sit in
training while the other is tested would score the router on a question it
has already seen, in another language.
"""

from __future__ import annotations

import random
from collections.abc import Sequence

import numpy as np

from scripts.metric_validation import stats
from scripts.router import logreg
from scripts.router.data import Example

LAMBDA_GRID: tuple[float, ...] = (0.01, 0.1, 1.0, 10.0)
SEED = 20260930


def folds(examples: Sequence[Example], k: int = 5, seed: int = SEED) -> list[int]:
    by_task: dict[str, list[str]] = {}
    for e in examples:
        by_task.setdefault(e.task_type, [])
        if e.prompt_id not in by_task[e.task_type]:
            by_task[e.task_type].append(e.prompt_id)
    assignment: dict[str, int] = {}
    for task in sorted(by_task):
        ids = sorted(by_task[task])
        random.Random(f"{seed}:{task}").shuffle(ids)
        for index, prompt_id in enumerate(ids):
            assignment[prompt_id] = index % k
    return [assignment[e.prompt_id] for e in examples]


def out_of_fold(X: np.ndarray, y: np.ndarray, fold_of: Sequence[int], lam: float) -> np.ndarray:
    fold_of = np.asarray(fold_of)
    p = np.zeros(len(y))
    for f in sorted(set(fold_of.tolist())):
        test = fold_of == f
        w, b = logreg.fit(X[~test], y[~test], lam)
        p[test] = logreg.predict(w, b, X[test])
    return p


def choose_lambda(
    X: np.ndarray, y: np.ndarray, fold_of: Sequence[int], grid: Sequence[float] = LAMBDA_GRID
) -> tuple[float, dict[float, float]]:
    losses = {lam: logreg.log_loss(y, out_of_fold(X, y, fold_of, lam)) for lam in grid}
    return min(losses, key=losses.get), losses


def auc(y: np.ndarray, p: np.ndarray) -> float:
    return stats.roc_auc(p.tolist(), [bool(v) for v in y])
