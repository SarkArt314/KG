from __future__ import annotations

import time
from typing import Any, Callable, Tuple

from . import algorithms


def measure_once(func: Callable[..., Any], *args: Any) -> Tuple[Any, dict]:
    """Замер времени одного вызова алгоритма."""
    start = time.perf_counter_ns()
    result = func(*args)
    elapsed = time.perf_counter_ns() - start

    info = {
        "points": len(result),
        "time_ns": elapsed,
        "time_ms": elapsed / 1_000_000,
    }

    return result, info


def benchmark(
    func: Callable[..., Any],
    args: tuple,
    min_total_ns: int = 50_000_000,
    max_repeats: int = 20_000,
) -> dict:
    """
    Бенчмарк алгоритма.
    Подбирает количество повторений так, чтобы суммарное время было
    не меньше min_total_ns. Это даёт более устойчивые замеры.
    """
    func(*args)

    repeats = 1
    total = 0

    while True:
        start = time.perf_counter_ns()

        for _ in range(repeats):
            func(*args)

        total = time.perf_counter_ns() - start

        if total >= min_total_ns or repeats >= max_repeats:
            break

        if total <= 0:
            repeats = min(max_repeats, repeats * 2)
        else:
            estimate = int((min_total_ns / total) * repeats)
            repeats = min(max_repeats, max(repeats + 1, estimate))

    result = func(*args)

    return {
        "repeats": repeats,
        "total_ns": total,
        "total_ms": total / 1_000_000,
        "avg_ns": total / repeats,
        "avg_ms": total / repeats / 1_000_000,
        "points": len(result),
    }


def benchmark_all(
    line_args: tuple = (0, 0, 160, 100),
    circle_args: tuple = (0, 0, 80),
    min_total_ns: int = 50_000_000,
) -> dict:
    """Бенчмарк всех четырёх алгоритмов."""
    data = {}

    for key, func in algorithms.LINE_ALGORITHMS.items():
        data[key] = benchmark(func, tuple(line_args), min_total_ns=min_total_ns)

    data["bresenham_circle"] = benchmark(
        algorithms.bresenham_circle,
        tuple(circle_args),
        min_total_ns=min_total_ns,
    )

    return data
