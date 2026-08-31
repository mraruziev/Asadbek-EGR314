from __future__ import annotations

import pytest

from leaf_ai.advice import ADVICE, HEALTHY, NOT_A_LEAF, advice_for


def test_every_advice_entry_is_populated():
    for name, advice in ADVICE.items():
        assert advice.cause, name
        assert advice.actions, name
        assert advice.urgency in {"none", "routine", "urgent"}, name


def test_fast_moving_diseases_are_flagged_urgent():
    for name in (
        "Tomato_Late_blight",
        "Potato_Late_blight",
        "Orange_Haunglongbing_Citrus_greening",
        "Tomato_Tomato_Yellow_Leaf_Curl_Virus",
    ):
        assert advice_for(name).urgency == "urgent", name


def test_slow_diseases_are_not_flagged_urgent():
    for name in ("Apple_Apple_scab", "Squash_Powdery_mildew", "Corn_maize_Common_rust"):
        assert advice_for(name).urgency == "routine", name


@pytest.mark.parametrize("name", ["Tomato_healthy", "Apple_healthy", "Soybean_healthy"])
def test_healthy_classes_share_the_healthy_entry(name):
    assert advice_for(name) is HEALTHY
    assert advice_for(name).urgency == "none"


def test_reject_class_gets_retake_guidance():
    assert advice_for("Not_a_leaf") is NOT_A_LEAF


def test_upstream_triple_underscore_names_resolve():
    assert advice_for("Tomato___Late_blight").urgency == "urgent"


def test_unknown_class_still_returns_usable_actions():
    """The catch-all must give the user something to do, not an apology."""
    advice = advice_for("Kumquat_mystery_condition")
    assert advice.urgency == "routine"
    assert advice.actions
    assert "extension service" in " ".join(advice.actions)


def test_keyword_rules_separate_downy_from_powdery_mildew():
    """They need different fungicides, so this must not collapse to one entry."""
    downy = advice_for("Basil_downy_mildew")
    powdery = advice_for("Cucumber_powdery_mildew")
    assert downy != powdery
    assert downy.urgency == "urgent"
    assert "oomycete-active" in " ".join(downy.actions).lower()


def test_every_trained_class_has_advice():
    """Nothing the model can predict should fall through to the placeholder."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "data/processed/plantvillage_cls/train"
    if not root.is_dir():
        pytest.skip("dataset not built")
    missing = [
        d.name
        for d in root.iterdir()
        if d.is_dir() and "No guidance" in advice_for(d.name).cause
    ]
    assert not missing, f"classes without advice: {missing}"
