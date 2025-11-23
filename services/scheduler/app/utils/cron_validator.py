"""
Utility functions for validating cron expressions based on user tiers.
"""

from datetime import datetime
from typing import Optional

from croniter import croniter

# Minimum intervals in seconds
FREE_TIER_MIN_INTERVAL = 5 * 60  # 5 minutes
PRO_TIER_MIN_INTERVAL = 5  # 5 seconds


def get_user_tier(user) -> str:
    """
    Get user tier from user metadata.

    Checks app_metadata first, then user_metadata for 'tier' or 'plan' field.
    Defaults to 'free' if not found.

    Args:
        user: User instance with app_metadata and user_metadata

    Returns:
        'pro' or 'free'
    """
    if not user:
        return "free"

    # Check app_metadata first (typically set by admin/system)
    if user.app_metadata:
        tier = user.app_metadata.get("tier") or user.app_metadata.get("plan")
        if tier:
            return tier.lower()

    # Check user_metadata
    if user.user_metadata:
        tier = user.user_metadata.get("tier") or user.user_metadata.get("plan")
        if tier:
            return tier.lower()

    # Default to free tier
    return "free"


def get_minimum_interval_for_tier(tier: str) -> int:
    """
    Get minimum interval in seconds for a given tier.

    Args:
        tier: User tier ('free' or 'pro')

    Returns:
        Minimum interval in seconds
    """
    tier_lower = tier.lower()
    if tier_lower == "pro":
        return PRO_TIER_MIN_INTERVAL
    return FREE_TIER_MIN_INTERVAL


def calculate_min_interval_from_cron(cron_expr: str, base_time: Optional[datetime] = None) -> int:
    """
    Calculate the minimum interval between executions for a cron expression.

    This function calculates the minimum time between consecutive executions
    by checking the next several execution times and finding the smallest gap.

    Args:
        cron_expr: Cron expression string
        base_time: Base time to start calculation from (defaults to now)

    Returns:
        Minimum interval in seconds between executions

    Raises:
        ValueError: If cron expression is invalid
    """
    if base_time is None:
        base_time = datetime.utcnow()

    try:
        cron = croniter(cron_expr, base_time)
    except Exception as e:
        raise ValueError(f"Invalid cron expression: {str(e)}")

    # Get next several execution times to find minimum interval
    execution_times = []
    # current_time = base_time  # type: ignore

    # Check up to 100 future executions or until we have enough data
    for _ in range(100):
        try:
            next_time = cron.get_next(datetime)
            execution_times.append(next_time)
            # current_time = next_time  # type: ignore
        except Exception:
            break

    if len(execution_times) < 2:
        # If we can't get multiple executions, assume it's a valid interval
        # This handles one-time or very infrequent schedules
        return 0

    # Calculate intervals between consecutive executions
    intervals = []
    for i in range(1, len(execution_times)):
        delta = execution_times[i] - execution_times[i - 1]
        intervals.append(int(delta.total_seconds()))

    if not intervals:
        return 0

    # Return the minimum interval found
    return min(intervals)


def validate_cron_interval(cron_expr: str, user, base_time: Optional[datetime] = None) -> None:
    """
    Validate that a cron expression meets the minimum interval requirement for the user's tier.

    Args:
        cron_expr: Cron expression string
        user: User instance to determine tier
        base_time: Base time for calculation (defaults to now)

    Raises:
        ValueError: If cron expression is invalid or doesn't meet minimum interval
    """
    # Get user tier and minimum interval
    tier = get_user_tier(user)
    min_required = get_minimum_interval_for_tier(tier)

    # Calculate actual minimum interval from cron expression
    try:
        actual_min = calculate_min_interval_from_cron(cron_expr, base_time)
    except ValueError as e:
        raise ValueError(f"Invalid cron expression: {str(e)}")

    # Special case: if actual_min is 0, it might be a one-time or very infrequent schedule
    # We'll allow it but check if the first execution is too soon
    if actual_min == 0:
        try:
            cron = croniter(cron_expr, base_time or datetime.utcnow())
            next_run = cron.get_next(datetime)
            time_until_next = (next_run - (base_time or datetime.utcnow())).total_seconds()  # type: ignore

            # If next execution is within the minimum interval, reject it
            if 0 < time_until_next < min_required:
                raise ValueError(
                    f"Schedule interval too frequent. Minimum interval for {tier} tier is "
                    f"{min_required} seconds ({min_required // 60} minutes). "
                    f"Next execution would be in {int(time_until_next)} seconds."
                )
        except Exception:
            pass
        return

    # Check if actual minimum interval meets requirement
    if actual_min < min_required:
        tier_name = "free" if tier == "free" else "pro"
        min_minutes = min_required // 60
        # min_seconds = min_required % 60 # type: ignore

        if min_required >= 60:
            interval_str = f"{min_minutes} minute{'s' if min_minutes > 1 else ''}"
        else:
            interval_str = f"{min_required} second{'s' if min_required > 1 else ''}"

        raise ValueError(
            f"Schedule interval too frequent for {tier_name} tier. "
            f"Minimum interval is {interval_str}. "
            f"Your schedule has a minimum interval of {actual_min} seconds."
        )
