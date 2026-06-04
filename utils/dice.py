"""Dice rolling utilities for the adventure game."""

import random


def roll_d20() -> tuple[int, str]:
    """Roll a D20 and return the raw roll plus outcome label."""
    roll = random.randint(1, 20)

    if roll <= 5:
        outcome = "Failure"
    elif roll <= 10:
        outcome = "Partial Success"
    elif roll <= 15:
        outcome = "Success"
    else:
        outcome = "Great Success"

    return roll, outcome
