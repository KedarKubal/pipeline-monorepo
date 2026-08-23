"""Row-level validation and quarantine logic.

Design choice: invalid rows are *quarantined* (split off with a reason),
not silently dropped and not allowed to crash the whole batch. A migration
run should tell you exactly which legacy records it couldn't place, so a
human can decide what to do with them.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from src.transform.cleaners import is_valid_email


@dataclass
class ValidationResult:
    valid: pd.DataFrame
    quarantined: pd.DataFrame  # same columns as input + a 'rejection_reason' column
    stats: dict[str, int] = field(default_factory=dict)

    def summary(self) -> str:
        return (
            f"valid={len(self.valid)} "
            f"quarantined={len(self.quarantined)} "
            f"({', '.join(f'{k}={v}' for k, v in self.stats.items()) or 'no rejections'})"
        )


def validate_customers(df: pd.DataFrame) -> ValidationResult:
    """Rejects rows with missing legacy_id, missing/invalid email, or missing last_name.

    Email is the target schema's uniqueness/business key downstream, so an
    invalid or missing email is a hard rejection rather than a warning.
    """
    reasons = pd.Series([None] * len(df), index=df.index, dtype="object")

    missing_id = df["customer_id"].isna() | (df["customer_id"].astype(str).str.strip() == "")
    reasons[missing_id] = "missing customer_id"

    bad_email = ~df["email"].apply(is_valid_email)
    reasons[bad_email & reasons.isna()] = "missing or invalid email"

    missing_name = (df["first_name"].str.strip() == "") & reasons.isna()
    reasons[missing_name] = "missing name"

    is_invalid = reasons.notna()
    quarantined = df[is_invalid].copy()
    quarantined["rejection_reason"] = reasons[is_invalid]

    valid = df[~is_invalid].copy()

    # Dedup on email — keep the most recently signed-up record, since a
    # duplicate email in the legacy export usually means a re-registration.
    dup_mask = valid.duplicated(subset=["email"], keep="last")
    newly_quarantined = valid[dup_mask].copy()
    newly_quarantined["rejection_reason"] = "duplicate email (kept most recent)"
    quarantined = pd.concat([quarantined, newly_quarantined], ignore_index=True)
    valid = valid[~dup_mask]

    stats = quarantined["rejection_reason"].value_counts().to_dict() if len(quarantined) else {}
    return ValidationResult(valid=valid, quarantined=quarantined, stats=stats)


def validate_order_lines(df: pd.DataFrame, known_customer_legacy_ids: set[str]) -> ValidationResult:
    """Rejects order lines with an unknown customer, non-positive quantity,
    negative price, or unparsable order_date — all of which would violate
    referential integrity or basic sanity in the target schema.
    """
    reasons = pd.Series([None] * len(df), index=df.index, dtype="object")

    orphaned = ~df["cust_id"].astype(str).isin(known_customer_legacy_ids)
    reasons[orphaned] = "customer not found (referential integrity)"

    bad_qty = (df["qty"].isna() | (df["qty"] <= 0)) & reasons.isna()
    reasons[bad_qty] = "invalid quantity"

    bad_price = (df["unit_price"].isna() | (df["unit_price"] < 0)) & reasons.isna()
    reasons[bad_price] = "invalid unit_price"

    bad_date = df["order_date"].isna() & reasons.isna()
    reasons[bad_date] = "unparsable order_date"

    is_invalid = reasons.notna()
    quarantined = df[is_invalid].copy()
    quarantined["rejection_reason"] = reasons[is_invalid]
    valid = df[~is_invalid].copy()

    stats = quarantined["rejection_reason"].value_counts().to_dict() if len(quarantined) else {}
    return ValidationResult(valid=valid, quarantined=quarantined, stats=stats)



VALID_AUDIT_ACTIONS = {"create", "update", "toggle", "delete"}


def validate_flag_audit(df: pd.DataFrame) -> ValidationResult:
    """Rejects audit rows with an unrecognized action, missing flag_key, or
    an unparsable changed_at — the three things that would make this row
    meaningless or unsafe to upsert as a FlagChangeAudit record.
    """
    reasons = pd.Series([None] * len(df), index=df.index, dtype="object")

    missing_key = df["flag_key"].isna() | (df["flag_key"].astype(str).str.strip() == "")
    reasons[missing_key] = "missing flag_key"

    bad_action = ~df["action"].isin(VALID_AUDIT_ACTIONS) & reasons.isna()
    reasons[bad_action] = "unrecognized action"

    bad_date = df["changed_at"].isna() & reasons.isna()
    reasons[bad_date] = "unparsable changed_at"

    is_invalid = reasons.notna()
    quarantined = df[is_invalid].copy()
    quarantined["rejection_reason"] = reasons[is_invalid]
    valid = df[~is_invalid].copy()

    dup_mask = valid.duplicated(subset=["flag_key", "changed_at"], keep="last")
    newly_quarantined = valid[dup_mask].copy()
    newly_quarantined["rejection_reason"] = "duplicate (flag_key, changed_at)"
    quarantined = pd.concat([quarantined, newly_quarantined], ignore_index=True)
    valid = valid[~dup_mask]

    stats = quarantined["rejection_reason"].value_counts().to_dict() if len(quarantined) else {}
    return ValidationResult(valid=valid, quarantined=quarantined, stats=stats)
