"""
SubZero — Policy & Payoff Decision Engine
==========================================
Uses Muse Spark Open (1026) on Baseten to:
  1. Run Chain-of-Verification (CoVe) reasoning over contract + usage data
  2. Compute Net Present Value (NPV) of each possible action
  3. Output one of: IMMEDIATE_CANCEL | DOWNGRADE_TIER | SCHEDULE_NOTICE |
                    RENEGOTIATE | PROTECT (headless bot / active dependency)
"""

import os
import json
import httpx
from datetime import date, datetime
from pydantic import BaseModel
from typing import Optional, Literal


# ── Request / Response Models ─────────────────────────────────────────────────
class DecisionRequest(BaseModel):
    subscription_id: str
    vendor_name: str
    monthly_cost_usd: float
    seat_count: int
    active_human_logins_last_90d: int
    has_webhook_dependency: bool
    is_headless_service_account: bool
    auto_renewal_date: Optional[str] = None        # ISO 8601
    cancellation_notice_window_days: Optional[int] = 0
    early_termination_fee_usd: Optional[float] = 0.0
    contract_term_months: Optional[int] = None
    months_remaining: Optional[int] = None
    governing_cancellation_clause: Optional[str] = None
    today_date: Optional[str] = None               # ISO 8601, defaults to today


ActionType = Literal[
    "IMMEDIATE_CANCEL",
    "DOWNGRADE_TIER",
    "SCHEDULE_NOTICE",
    "RENEGOTIATE",
    "PROTECT",
]


class PayoffSummary(BaseModel):
    action: ActionType
    net_savings_usd: float
    cost_of_action_usd: float
    months_to_break_even: Optional[float]
    notice_deadline: Optional[str]     # ISO 8601 date
    confidence: float                  # 0.0 – 1.0
    reasoning_trace: str               # Chain-of-Verification steps
    alert_message: Optional[str] = None


# ── Decision Engine ────────────────────────────────────────────────────────────
class DecisionEngine:
    """
    Deterministic NPV solver + Muse Spark Open CoVe reasoner.
    The deterministic layer catches the hard-coded traps (bot accounts, imminent
    notice deadlines). Muse Spark Open handles ambiguous cases and generates the
    human-readable reasoning trace.
    """

    BASETEN_API_KEY   = os.getenv("BASETEN_API_KEY", "")
    BASETEN_MODEL_ID  = os.getenv("BASETEN_MODEL_ID", "meta-models/muse-spark-open-1026")
    BASETEN_API_BASE  = os.getenv("BASETEN_API_BASE", "https://api.baseten.co/v1")

    def __init__(self):
        self.http = httpx.AsyncClient(timeout=90.0)

    # ── Public ────────────────────────────────────────────────────────────────
    async def evaluate(self, req: DecisionRequest) -> dict:
        today = date.fromisoformat(req.today_date) if req.today_date else date.today()

        # ── Guard Rails (Deterministic, cannot be overridden by LLM) ─────────
        if req.is_headless_service_account or req.has_webhook_dependency:
            return PayoffSummary(
                action="PROTECT",
                net_savings_usd=0.0,
                cost_of_action_usd=0.0,
                months_to_break_even=None,
                notice_deadline=None,
                confidence=1.0,
                reasoning_trace=(
                    "[TRAP DETECTED] subscription_id={sub} — is_headless_service_account={bot} | "
                    "has_webhook_dependency={hook}. Cancellation would break automated pipelines. "
                    "Action: PROTECT. No further steps taken."
                ).format(
                    sub=req.subscription_id,
                    bot=req.is_headless_service_account,
                    hook=req.has_webhook_dependency,
                ),
                alert_message="⚠️ Headless bot or webhook dependency detected. Protected from cancellation.",
            ).model_dump()

        # ── NPV Calculation ────────────────────────────────────────────────────
        etf  = req.early_termination_fee_usd or 0.0
        mnth = req.months_remaining or (req.contract_term_months or 12)
        total_remaining_cost = req.monthly_cost_usd * mnth
        net_savings_if_cancel_now = total_remaining_cost - etf

        # Notice window check
        notice_deadline = None
        notice_days_left = None
        if req.auto_renewal_date and req.cancellation_notice_window_days:
            renewal = date.fromisoformat(req.auto_renewal_date)
            from datetime import timedelta
            notice_deadline_dt = renewal - timedelta(days=req.cancellation_notice_window_days)
            notice_deadline = notice_deadline_dt.isoformat()
            notice_days_left = (notice_deadline_dt - today).days

        # ── Determine Candidate Action (Deterministic Rule Layer) ─────────────
        candidate_action: ActionType
        alert = None

        if req.active_human_logins_last_90d == 0 and etf == 0:
            candidate_action = "IMMEDIATE_CANCEL"
        elif req.active_human_logins_last_90d == 0 and etf > 0:
            # ETF trap: is it cheaper to wait for notice window?
            if notice_days_left is not None and notice_days_left > 0:
                candidate_action = "SCHEDULE_NOTICE"
                alert = (
                    f"⚠️ Early termination fee of ${etf:,.0f} detected! "
                    f"File notice by {notice_deadline} ({notice_days_left} days) "
                    f"to avoid the fee and save ${total_remaining_cost:,.0f}."
                )
            elif notice_days_left is not None and notice_days_left <= 0:
                alert = (
                    f"🚨 Auto-renewal notice deadline has PASSED (was {notice_deadline}). "
                    f"Company is locked in for another term. Initiating renegotiation."
                )
                candidate_action = "RENEGOTIATE"
            else:
                candidate_action = "IMMEDIATE_CANCEL" if net_savings_if_cancel_now > 0 else "SCHEDULE_NOTICE"
        elif req.active_human_logins_last_90d > 0 and req.seat_count > req.active_human_logins_last_90d:
            candidate_action = "DOWNGRADE_TIER"
        else:
            candidate_action = "RENEGOTIATE"

        # ── Muse Spark Open: Generate Reasoning Trace ─────────────────────────
        reasoning = await self._muse_spark_reason(req, candidate_action, net_savings_if_cancel_now, notice_deadline)

        return PayoffSummary(
            action=candidate_action,
            net_savings_usd=max(net_savings_if_cancel_now, 0.0),
            cost_of_action_usd=etf,
            months_to_break_even=(etf / req.monthly_cost_usd) if req.monthly_cost_usd > 0 else None,
            notice_deadline=notice_deadline,
            confidence=0.92,
            reasoning_trace=reasoning,
            alert_message=alert,
        ).model_dump()

    # ── Muse Spark Open: CoVe Reasoning Trace ─────────────────────────────────
    async def _muse_spark_reason(
        self,
        req: DecisionRequest,
        action: ActionType,
        net_savings: float,
        notice_deadline: Optional[str],
    ) -> str:
        system_prompt = (
            "You are SubZero, a verifiable enterprise SaaS deprovisioning agent. "
            "Given subscription data and a candidate action, produce a concise "
            "Chain-of-Verification (CoVe) reasoning trace. "
            "Format:\n"
            "  [STEP 1] State what was checked and why\n"
            "  [STEP 2] State the financial calculation\n"
            "  [STEP 3] State the safety check result\n"
            "  [VERDICT] Final action and justification\n"
            "Be precise. No hallucinations. If data is missing, state it explicitly."
        )

        user_message = json.dumps({
            "subscription_id": req.subscription_id,
            "vendor": req.vendor_name,
            "monthly_cost_usd": req.monthly_cost_usd,
            "seat_count": req.seat_count,
            "active_human_logins_last_90d": req.active_human_logins_last_90d,
            "early_termination_fee_usd": req.early_termination_fee_usd,
            "auto_renewal_date": req.auto_renewal_date,
            "cancellation_notice_window_days": req.cancellation_notice_window_days,
            "candidate_action": action,
            "calculated_net_savings_usd": round(net_savings, 2),
            "notice_deadline": notice_deadline,
        }, indent=2)

        try:
            response = await self.http.post(
                f"{self.BASETEN_API_BASE}/chat/completions",
                json={
                    "model": self.BASETEN_MODEL_ID,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": user_message},
                    ],
                    "max_tokens": 512,
                    "temperature": 0.1,   # Low temperature for deterministic reasoning
                },
                headers={
                    "Authorization": f"Api-Key {self.BASETEN_API_KEY}",
                    "Content-Type":  "application/json",
                },
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

        except Exception as e:
            print(f"[Muse Spark Open] Reasoning error: {e}")
            return (
                f"[STEP 1] Subscription {req.subscription_id} — vendor: {req.vendor_name}\n"
                f"[STEP 2] Monthly cost: ${req.monthly_cost_usd:.2f} | "
                f"ETF: ${req.early_termination_fee_usd:.2f} | "
                f"Net savings: ${net_savings:.2f}\n"
                f"[STEP 3] Human logins (90d): {req.active_human_logins_last_90d} | "
                f"Headless bot: {req.is_headless_service_account}\n"
                f"[VERDICT] {action} — calculated deterministically (LLM trace unavailable)."
            )
