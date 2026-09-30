"""L2-regularised logistic regression by Newton's method (IRLS).

768 features and ~1000 training rows: the Hessian is small enough to solve
exactly, so there is no learning rate to tune and the fit is deterministic.
"""

from __future__ import annotations

import numpy as np


def _sigmoid(z: np.ndarray) -> np.ndarray:
    return 0.5 * (1.0 + np.tanh(0.5 * z))


def fit(X: np.ndarray, y: np.ndarray, lam: float, iters: int = 50) -> tuple[np.ndarray, float]:
    n, d = X.shape
    A = np.hstack([X, np.ones((n, 1))])
    theta = np.zeros(d + 1)
    reg = np.full(d + 1, lam)
    reg[-1] = 0.0  # the bias is not shrunk
    for _ in range(iters):
        p = _sigmoid(A @ theta)
        grad = A.T @ (p - y) / n + reg * theta
        hess = (A.T * (p * (1 - p))) @ A / n + np.diag(reg) + 1e-9 * np.eye(d + 1)
        step = np.linalg.solve(hess, grad)
        theta -= step
        if np.max(np.abs(step)) < 1e-8:
            break
    return theta[:-1], float(theta[-1])


def predict(w: np.ndarray, b: float, X: np.ndarray) -> np.ndarray:
    return _sigmoid(X @ w + b)


def log_loss(y: np.ndarray, p: np.ndarray) -> float:
    p = np.clip(p, 1e-12, 1 - 1e-12)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))
