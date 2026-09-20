from analysis.directional_contract import (
    BEARISH_THRESHOLD,
    BULLISH_THRESHOLD,
    classify_direction,
    combined_structure_score,
    conflict_state,
    evidence,
    normalize_signed_score,
    vote_counts,
)


def test_direction_contract_uses_shared_boundaries():
    assert classify_direction(BULLISH_THRESHOLD) == "bullish"
    assert classify_direction(BEARISH_THRESHOLD) == "bearish"
    assert classify_direction(50.0) == "neutral"


def test_signed_score_normalization_is_symmetric():
    assert normalize_signed_score(-20.0) == 40.0
    assert normalize_signed_score(0.0) == 50.0
    assert normalize_signed_score(20.0) == 60.0


def test_structure_blend_keeps_local_bos_visible_against_context():
    assert combined_structure_score(20.0, -20.0) == 8.0
    assert combined_structure_score(-20.0, 20.0) == -8.0


def test_conflict_uses_same_ten_component_semantics():
    components = {
        "smart_money": 10.0,
        "structure": 8.0,
        "price_action": 0.0,
        "supply_demand": 20.0,
        "momentum": 10.0,
        "candlestick": 10.0,
        "elliott": 15.0,
        "harmonic": 0.0,
        "brooks": 0.0,
        "wyckoff": 0.0,
    }
    assert vote_counts(components) == (6, 0, 4)
    assert conflict_state(components) == "CONSENSUS"


def test_evidence_strength_is_zero_at_neutral():
    result = evidence(0.0)
    assert result.direction == "neutral"
    assert result.strength == 0.0
