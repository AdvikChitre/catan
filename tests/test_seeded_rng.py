"""Tests for deterministic seeded RNG behavior."""

from src.simulation.seeded_rng import SeededRng


class TestSeededRng:
    def test_seeded_rng_reproducible_sequences(self):
        rng_a = SeededRng(42)
        rng_b = SeededRng(42)

        seq_a = [rng_a.randint(0, 100) for _ in range(20)]
        seq_b = [rng_b.randint(0, 100) for _ in range(20)]

        assert seq_a == seq_b

    def test_seeded_rng_choice_and_shuffle_are_reproducible(self):
        first = SeededRng(7)
        second = SeededRng(7)

        items_a = ["a", "b", "c", "d", "e"]
        items_b = ["a", "b", "c", "d", "e"]

        first.shuffle(items_a)
        second.shuffle(items_b)

        assert items_a == items_b
        assert first.choice(items_a) == second.choice(items_b)

    def test_seeded_rng_uses_seed_value(self):
        rng_a = SeededRng(99)
        rng_b = SeededRng(100)

        assert rng_a.randint(0, 1000) != rng_b.randint(0, 1000)

    def test_seeded_rng_default_seed_is_stored(self):
        rng = SeededRng()

        assert isinstance(rng.seed, int)
        assert rng.seed >= 0
        assert hasattr(rng, "rng")
