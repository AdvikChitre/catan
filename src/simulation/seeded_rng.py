"""Seeded random number generator"""
import random
from typing import Optional


class SeededRng:
    """Deterministic seeded random number generator"""
    def __init__(self, seed: Optional[int] = None):
        self.seed = seed if seed is not None else random.randint(0, 2**31 - 1)
        self.rng = random.Random(self.seed)

    def randint(self, a: int, b: int) -> int:
        """Return a random integer N such that a <= N <= b"""
        return self.rng.randint(a, b)

    def shuffle(self, seq: list) -> None:
        """Shuffle list in place"""
        self.rng.shuffle(seq)

    def choice(self, seq: list):
        """Return a random element from the non-empty sequence"""
        return self.rng.choice(seq)
