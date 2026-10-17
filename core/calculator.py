"""High-precision calculation engine for peer evaluation using Decimal arithmetic."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, ROUND_FLOOR
from typing import Dict, List, Optional, Set

DECIMAL_ZERO = Decimal("0")
DECIMAL_ONE = Decimal("1")
DECIMAL_TEN = Decimal("10.0")
DECIMAL_HUNDRED = Decimal("100.0")
PRECISION_2DP = Decimal("0.01")
PRECISION_4DP = Decimal("0.0001")


def to_decimal(val: object) -> Decimal:
    """Safely convert any numeric / string input to Decimal."""
    if isinstance(val, Decimal):
        return val
    return Decimal(str(val))


def quantize_2dp(val: Decimal) -> Decimal:
    """Round to 2 decimal places using ROUND_HALF_UP."""
    return val.quantize(PRECISION_2DP, rounding=ROUND_HALF_UP)


@dataclass
class MemberScore:
    member_id: int
    raw_r: Decimal
    final_r: Decimal
    raw_score: Decimal
    final_score: Decimal
    percentage: Decimal
    is_missing: bool


@dataclass
class CalculationResult:
    group_score_x: Decimal
    total_budget: Decimal
    group_average: Decimal
    member_scores: Dict[int, MemberScore]
    missing_evaluators: List[int]
    active_evaluators: List[int]


def calculate_final_scores(
    group_score_x: object,
    evaluations: Dict[int, Dict[int, object]],
    member_ids: List[int],
    penalty_ratio: object = 0.0,
    max_score_cap: object = 10.0,
    min_score_floor: object = 0.0,
) -> CalculationResult:
    """
    Calculate individual final scores based on peer evaluations.

    Args:
        group_score_x: Group base score given by instructor (e.g. 8.5).
        evaluations: Dict mapping evaluator_id -> {target_id: score_pct (e.g. 100.0)}.
        member_ids: List of all valid member IDs in the group.
        penalty_ratio: Percentage penalty for members who failed to submit (e.g. 0.1 for 10%).
        max_score_cap: Upper ceiling for individual score (default 10.0).
        min_score_floor: Lower floor for individual score (default 0.0).
    """
    score_x = to_decimal(group_score_x)
    penalty_rate = to_decimal(penalty_ratio)
    cap = to_decimal(max_score_cap)
    floor = to_decimal(min_score_floor)

    n = len(member_ids)
    if n == 0:
        raise ValueError("Danh sách thành viên không được rỗng.")

    total_budget = Decimal(n) * score_x

    # Single-member group edge case
    if n == 1:
        single_id = member_ids[0]
        final_sc = min(cap, max(floor, score_x))
        return CalculationResult(
            group_score_x=score_x,
            total_budget=total_budget,
            group_average=quantize_2dp(final_sc),
            member_scores={
                single_id: MemberScore(
                    member_id=single_id,
                    raw_r=DECIMAL_ONE,
                    final_r=DECIMAL_ONE,
                    raw_score=final_sc,
                    final_score=quantize_2dp(final_sc),
                    percentage=DECIMAL_HUNDRED,
                    is_missing=False,
                )
            },
            missing_evaluators=[],
            active_evaluators=[single_id],
        )

    # Step 0: Default Imputation (100% for missing evaluators)
    complete_evaluations: Dict[int, Dict[int, Decimal]] = {}
    missing_evaluators: List[int] = []
    active_evaluators: List[int] = []

    for uid in member_ids:
        user_eval = evaluations.get(uid)
        # Check if evaluator submitted valid ratings for peers
        if user_eval and len(user_eval) > 0:
            active_evaluators.append(uid)
            complete_evaluations[uid] = {
                t_id: to_decimal(s)
                for t_id, s in user_eval.items()
                if t_id != uid and t_id in member_ids
            }
            # Fill missing peer ratings from an active evaluator with 100% if omitted
            for peer_id in member_ids:
                if peer_id != uid and peer_id not in complete_evaluations[uid]:
                    complete_evaluations[uid][peer_id] = DECIMAL_HUNDRED
        else:
            missing_evaluators.append(uid)
            # Default Imputation: 100% to all peers
            complete_evaluations[uid] = {
                target: DECIMAL_HUNDRED
                for target in member_ids
                if target != uid
            }

    # Step 1: Compute R_i (Sum received / (N - 1))
    divisor = Decimal(n - 1)
    sum_received: Dict[int, Decimal] = {i: DECIMAL_ZERO for i in member_ids}
    for evaluator_id, review in complete_evaluations.items():
        for target_id, score_pct in review.items():
            sum_received[target_id] += score_pct / DECIMAL_HUNDRED

    raw_r = {i: sum_received[i] / divisor for i in member_ids}
    r = dict(raw_r)

    # Step 1.1: Penalty for missing evaluators (if configured)
    if (
        penalty_rate > DECIMAL_ZERO
        and len(missing_evaluators) > 0
        and len(missing_evaluators) < n
    ):
        penalty_pool = DECIMAL_ZERO
        for uid in missing_evaluators:
            cut = r[uid] * penalty_rate
            r[uid] -= cut
            penalty_pool += cut

        bonus_per_active = penalty_pool / Decimal(len(active_evaluators))
        for uid in active_evaluators:
            r[uid] += bonus_per_active

    # Step 2: Preliminary scores
    scores = {i: score_x * r[i] for i in member_ids}

    # Step 3: Floor (0.0) clamping
    for i in member_ids:
        if scores[i] < floor:
            scores[i] = floor

    # Step 4: Iterative Cap (10.0) clamping and redistribution of excess
    active_pool: Set[int] = set(member_ids)
    while True:
        overflow_members = [i for i in active_pool if scores[i] > cap]
        if not overflow_members:
            break

        excess_points = DECIMAL_ZERO
        for i in overflow_members:
            excess_points += scores[i] - cap
            scores[i] = cap
            active_pool.remove(i)

        if not active_pool:
            # All members reached maximum cap
            break

        sum_active_r = sum(r[i] for i in active_pool)
        if sum_active_r > DECIMAL_ZERO:
            for i in active_pool:
                scores[i] += excess_points * (r[i] / sum_active_r)
        else:
            share = excess_points / Decimal(len(active_pool))
            for i in active_pool:
                scores[i] += share

    # Step 5: Exact 2-decimal-place rounding with Largest Remainder Adjustment
    # Target sum is the sum of exact scores (capped at N * cap)
    target_sum = quantize_2dp(sum(scores.values()))
    final_rounded = {i: quantize_2dp(scores[i]) for i in member_ids}
    current_sum = sum(final_rounded.values())
    cents_diff = int((target_sum - current_sum) * Decimal("100"))

    if cents_diff != 0:
        # Calculate remainder = raw_score - rounded_score
        remainders = [(i, scores[i] - final_rounded[i]) for i in member_ids]
        if cents_diff > 0:
            # Sort by largest positive remainder, add 0.01 to top cents_diff members
            remainders.sort(key=lambda x: x[1], reverse=True)
            for k in range(min(cents_diff, len(remainders))):
                uid = remainders[k][0]
                if final_rounded[uid] < cap:
                    final_rounded[uid] += PRECISION_2DP
        else:
            # Sort by smallest (most negative) remainder, subtract 0.01 from top abs(cents_diff) members
            remainders.sort(key=lambda x: x[1])
            for k in range(min(abs(cents_diff), len(remainders))):
                uid = remainders[k][0]
                if final_rounded[uid] > floor:
                    final_rounded[uid] -= PRECISION_2DP

    # Step 6: Final packaging
    member_scores: Dict[int, MemberScore] = {}
    for i in member_ids:
        pct = (
            quantize_2dp((final_rounded[i] / total_budget) * DECIMAL_HUNDRED)
            if total_budget > DECIMAL_ZERO
            else DECIMAL_ZERO
        )
        member_scores[i] = MemberScore(
            member_id=i,
            raw_r=raw_r[i].quantize(PRECISION_4DP, rounding=ROUND_HALF_UP),
            final_r=r[i].quantize(PRECISION_4DP, rounding=ROUND_HALF_UP),
            raw_score=scores[i],
            final_score=final_rounded[i],
            percentage=pct,
            is_missing=(i in missing_evaluators),
        )

    avg = quantize_2dp(sum(final_rounded.values()) / Decimal(n))

    return CalculationResult(
        group_score_x=score_x,
        total_budget=total_budget,
        group_average=avg,
        member_scores=member_scores,
        missing_evaluators=missing_evaluators,
        active_evaluators=active_evaluators,
    )
