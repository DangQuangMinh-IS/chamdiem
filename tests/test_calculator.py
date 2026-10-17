"""Unit tests for peer evaluation calculation engine."""

from decimal import Decimal
import pytest
from core.calculator import (
    calculate_final_scores,
    DECIMAL_ONE,
    DECIMAL_TEN,
    DECIMAL_ZERO,
)


def test_perfect_equality():
    """When all members evaluate each other at 100%, everyone receives group score X."""
    members = [1, 2, 3, 4, 5]
    group_score = Decimal("8.5")
    evaluations = {
        i: {j: Decimal("100.0") for j in members if j != i} for i in members
    }

    result = calculate_final_scores(group_score, evaluations, members)

    assert result.group_average == group_score
    for m in members:
        sc = result.member_scores[m]
        assert sc.final_r == DECIMAL_ONE
        assert sc.final_score == group_score
        assert sc.is_missing is False


def test_default_imputation_without_penalty():
    """Missing evaluators are auto-imputed with 100%, sum of scores is conserved."""
    members = [1, 2, 3, 4]
    group_score = Decimal("8.0")
    # Member 1 and 2 submit ratings, Member 3 and 4 forgot to submit
    evaluations = {
        1: {2: 120.0, 3: 90.0, 4: 90.0},
        2: {1: 110.0, 3: 95.0, 4: 95.0},
    }

    result = calculate_final_scores(
        group_score, evaluations, members, penalty_ratio=0.0
    )

    assert len(result.missing_evaluators) == 2
    assert set(result.missing_evaluators) == {3, 4}

    # Total budget must be conserved: N * X = 4 * 8.0 = 32.0
    total_score = sum(sc.final_score for sc in result.member_scores.values())
    assert total_score == Decimal("32.00")
    assert result.group_average == Decimal("8.00")


def test_penalty_redistribution():
    """Penalty on missing evaluators is deducted and redistributed to active ones."""
    members = [1, 2, 3, 4]
    group_score = Decimal("8.0")
    # Member 1, 2, 3 submit 100% to all; Member 4 does not submit
    evaluations = {
        1: {2: 100.0, 3: 100.0, 4: 100.0},
        2: {1: 100.0, 3: 100.0, 4: 100.0},
        3: {1: 100.0, 2: 100.0, 4: 100.0},
    }

    # 10% penalty
    result = calculate_final_scores(
        group_score, evaluations, members, penalty_ratio=0.1
    )

    sc4 = result.member_scores[4]
    assert sc4.is_missing is True
    assert sc4.final_score == Decimal("7.20")

    # The 0.1 penalty is divided among 3 active members: +0.0333 R each
    for m in [1, 2, 3]:
        scm = result.member_scores[m]
        assert scm.final_score > Decimal("8.00")

    # Budget conserved
    total_score = sum(sc.final_score for sc in result.member_scores.values())
    assert total_score == Decimal("32.00")


def test_all_missing_evaluators():
    """When all members forget to submit, all get 100% imputation and equal score X."""
    members = [1, 2, 3, 4, 5]
    group_score = Decimal("7.5")

    result = calculate_final_scores(
        group_score, {}, members, penalty_ratio=0.1
    )

    assert len(result.missing_evaluators) == 5
    # No active evaluators to receive penalty, so no penalty applied
    for m in members:
        assert result.member_scores[m].final_score == Decimal("7.50")
    assert result.group_average == Decimal("7.50")


def test_cap_10_overflow_redistribution():
    """Scores above 10.0 are capped and excess points redistributed to remaining members."""
    members = [1, 2, 3]
    group_score = Decimal("9.0")
    # Member 2 and 3 praise Member 1 excessively
    evaluations = {
        1: {2: 100.0, 3: 100.0},
        2: {1: 160.0, 3: 40.0},
        3: {1: 160.0, 2: 40.0},
    }

    result = calculate_final_scores(group_score, evaluations, members)

    sc1 = result.member_scores[1]
    assert sc1.final_score == Decimal("10.00")

    # Member 2 and 3 receive the excess points
    for m in [2, 3]:
        assert result.member_scores[m].final_score <= Decimal("10.00")

    total_score = sum(sc.final_score for sc in result.member_scores.values())
    assert total_score == Decimal("27.00")


def test_nine_member_team():
    """Simulate a realistic 9-member university team as in user prompt."""
    members = list(range(1, 10))
    group_score = Decimal("8.2")

    # 7 members submit, 2 missing
    evaluations = {}
    for i in range(1, 8):
        evaluations[i] = {j: 100.0 for j in members if j != i}
        # Give member 1 a boost and member 2 a slight reduction
        if i != 1 and i != 2:
            evaluations[i][1] = 110.0
            evaluations[i][2] = 90.0

    result = calculate_final_scores(
        group_score, evaluations, members, penalty_ratio=0.1
    )

    assert len(result.missing_evaluators) == 2
    assert set(result.missing_evaluators) == {8, 9}

    total_score = sum(sc.final_score for sc in result.member_scores.values())
    # 9 * 8.2 = 73.80
    assert total_score == Decimal("73.80")
    assert result.group_average == Decimal("8.20")


def test_single_member_group():
    """Single member group edge case."""
    result = calculate_final_scores(Decimal("9.2"), {}, [1])
    assert result.member_scores[1].final_score == Decimal("9.20")
    assert result.group_average == Decimal("9.20")
