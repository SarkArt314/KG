from __future__ import annotations

import math
from typing import Callable, Dict, List, Tuple

Point = Tuple[int, int]


def _iround(value: float) -> int:
    """
    Округление до ближайшего целого.
    Для положительных и отрицательных чисел используется симметричное
    округление от нуля при .5, чтобы поведение было предсказуемым.
    """
    if value >= 0:
        return int(math.floor(value + 0.5))
    return -int(math.floor(-value + 0.5))


def _unique(points: List[Point]) -> List[Point]:
    """Убирает дубликаты точек, сохраняя порядок."""
    seen = set()
    result = []
    for point in points:
        if point not in seen:
            seen.add(point)
            result.append(point)
    return result


def step_line(x0: int, y0: int, x1: int, y1: int) -> List[Point]:
    """
    Пошаговый алгоритм построения отрезка.
    Для устранения сильной зависимости от оси при крутых отрезках
    при необходимости меняем оси местами.
    """
    if x0 == x1 and y0 == y1:
        return [(x0, y0)]

    swapped = False
    ax0, ay0, ax1, ay1 = x0, y0, x1, y1

    if abs(ay1 - ay0) > abs(ax1 - ax0):
        ax0, ay0, ax1, ay1 = ay0, ax0, ay1, ax1
        swapped = True

    if ax0 > ax1:
        ax0, ax1, ay0, ay1 = ax1, ax0, ay1, ay0

    dx = ax1 - ax0
    dy = ay1 - ay0

    points: List[Point] = []

    if dx == 0:
        step = 1 if ay1 >= ay0 else -1
        for ay in range(ay0, ay1 + step, step):
            points.append((ay, ax0) if swapped else (ax0, ay))
        return points

    k = dy / dx
    b = ay0 - k * ax0

    for ax in range(ax0, ax1 + 1):
        ay = _iround(k * ax + b)
        if swapped:
            points.append((ay, ax))
        else:
            points.append((ax, ay))

    return points


def dda_line(x0: int, y0: int, x1: int, y1: int) -> List[Point]:
    """Алгоритм ЦДА (Digital Differential Analyzer)."""
    if x0 == x1 and y0 == y1:
        return [(x0, y0)]

    dx = x1 - x0
    dy = y1 - y0
    steps = max(abs(dx), abs(dy))

    if steps == 0:
        return [(x0, y0)]

    x_inc = dx / steps
    y_inc = dy / steps

    x = float(x0)
    y = float(y0)

    points: List[Point] = []

    for _ in range(steps + 1):
        points.append((_iround(x), _iround(y)))
        x += x_inc
        y += y_inc

    return points


def bresenham_line(x0: int, y0: int, x1: int, y1: int) -> List[Point]:
    """Целочисленный алгоритм Брезенхема для отрезка, для всех октантов."""
    points: List[Point] = []

    x = x0
    y = y0

    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)

    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1

    err = dx + dy

    while True:
        points.append((x, y))

        if x == x1 and y == y1:
            break

        e2 = 2 * err

        if e2 >= dy:
            err += dy
            x += sx

        if e2 <= dx:
            err += dx
            y += sy

    return points


def bresenham_circle(xc: int, yc: int, r: int) -> List[Point]:
    """Алгоритм Брезенхема для окружности по 8 октантам."""
    if r < 0:
        raise ValueError("Радиус не может быть отрицательным.")

    if r == 0:
        return [(xc, yc)]

    x = 0
    y = r
    d = 3 - 2 * r

    points: List[Point] = []

    while x <= y:
        points.extend(
            [
                (xc + x, yc + y),
                (xc + y, yc + x),
                (xc - x, yc + y),
                (xc - y, yc + x),
                (xc + x, yc - y),
                (xc + y, yc - x),
                (xc - x, yc - y),
                (xc - y, yc - x),
            ]
        )

        if d < 0:
            d += 4 * x + 6
        else:
            d += 4 * (x - y) + 10
            y -= 1

        x += 1

    return _unique(points)


LINE_ALGORITHMS: Dict[str, Callable[[int, int, int, int], List[Point]]] = {
    "step": step_line,
    "dda": dda_line,
    "bresenham_line": bresenham_line,
}

ALGORITHM_TITLES = {
    "step": "Пошаговый алгоритм (отрезок)",
    "dda": "Алгоритм ЦДА (отрезок)",
    "bresenham_line": "Алгоритм Брезенхема (отрезок)",
    "bresenham_circle": "Алгоритм Брезенхема (окружность)",
}
