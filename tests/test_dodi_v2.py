"""
The three rules of the v2 weighting, checked on numbers from the 2024 results.

Run from the repo root: python tests/test_dodi_v2.py (pytest also picks it up)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from dodi_v2 import score_v2


def test_no_promise_means_no_gap():
    # a subscription or a service that sells nothing has no ownership promise to break
    assert score_v2(99.5, 0.0, False) == 0.0


def test_one_time_purchase_keeps_the_contract_score():
    assert score_v2(94.1, 1.0, False) == 94.1


def test_buy_wording_on_a_subscription_halves_it():
    assert score_v2(95.7, 0.5, False) == 47.85


def test_licence_disclosure_at_checkout_halves_the_gap():
    assert score_v2(63.4, 1.0, True) == 31.7


if __name__ == "__main__":
    tests = [f for name, f in sorted(globals().items()) if name.startswith("test_")]
    for t in tests:
        t()
    print(f"{len(tests)} v2 checks passed")
