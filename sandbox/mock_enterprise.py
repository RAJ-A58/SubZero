"""
SubZero — Mock Enterprise Environment
=======================================
A pure-Python simulation of an enterprise identity and integration layer.
Used by sandbox_client.py when Modal remote sandboxes aren't available,
and by the Modal digital twin itself for its internal environment model.

Provides three adversarial subscriptions that mirror the EnvAudit traps:
  sw_101 — Genuine zombie license (safe to cancel)
  sw_204 — Headless CI/CD service account (TRAP: cancellation kills pipelines)
  sw_307 — Active user, annual contract with $1,800 ETF (TRAP: ETF penalty)
  sw_412 — Partially used enterprise seat (safe to downgrade)
"""

import random
from datetime import datetime, date, timedelta


# ── Subscription Registry ──────────────────────────────────────────────────────
SUBSCRIPTIONS = {
    "sw_101": {
        "vendor":                "Notion",
        "monthly_cost_usd":      120.00,
        "seat_count":            5,
        "active_human_logins":   0,          # Genuinely unused
        "is_headless_bot":       False,
        "has_webhook":           False,
        "user_type":             "human",
        "auto_renewal_date":     (date.today() + timedelta(days=45)).isoformat(),
        "notice_window_days":    30,
        "early_termination_fee": 0.0,
        "contract_term_months":  12,
        "months_remaining":      2,
        "clause":                "Section 9.1: Either party may terminate with 30 days written notice.",
    },
    "sw_204": {
        "vendor":                "Datadog",
        "monthly_cost_usd":      340.00,
        "seat_count":            1,
        "active_human_logins":   0,          # Looks dead — but it's a CI/CD bot!
        "is_headless_bot":       True,        # ← TRAP A
        "has_webhook":           True,
        "user_type":             "service_account",
        "auto_renewal_date":     (date.today() + timedelta(days=60)).isoformat(),
        "notice_window_days":    0,
        "early_termination_fee": 0.0,
        "contract_term_months":  12,
        "months_remaining":      5,
        "clause":                "Section 4.2: Month-to-month after initial term.",
        "active_webhooks":       [
            "github-actions/deploy-prod",
            "github-actions/run-tests",
            "pagerduty/alert-monitor",
        ],
    },
    "sw_307": {
        "vendor":                "Figma",
        "monthly_cost_usd":      200.00,
        "seat_count":            10,
        "active_human_logins":   0,          # Unused — but annual contract!
        "is_headless_bot":       False,
        "has_webhook":           False,
        "user_type":             "human",
        "auto_renewal_date":     (date.today() + timedelta(days=25)).isoformat(),
        "notice_window_days":    30,
        "early_termination_fee": 1800.00,    # ← TRAP B: ETF penalty
        "contract_term_months":  12,
        "months_remaining":      9,
        "clause":                "Section 12.3: Annual commitment. Early termination subject to remaining balance.",
    },
    "sw_412": {
        "vendor":                "Miro",
        "monthly_cost_usd":      180.00,
        "seat_count":            20,
        "active_human_logins":   7,          # 7 of 20 seats actually used
        "is_headless_bot":       False,
        "has_webhook":           False,
        "user_type":             "human",
        "auto_renewal_date":     (date.today() + timedelta(days=90)).isoformat(),
        "notice_window_days":    30,
        "early_termination_fee": 0.0,
        "contract_term_months":  12,
        "months_remaining":      6,
        "clause":                "Section 7.1: Tier downgrade permitted with 30 days notice.",
    },
}


# ── Mock Enterprise Environment Class ─────────────────────────────────────────
class MockEnterpriseEnv:
    """
    Provides three lookup methods that mirror a real Okta/GitHub enterprise:
      check_idp_sessions  → Simulates Okta SCIM token activity
      check_webhooks      → Simulates GitHub Actions / PagerDuty webhooks
      get_user_type       → Simulates software metadata registry
    """

    def check_idp_sessions(self, subscription_id: str) -> dict:
        sub = SUBSCRIPTIONS.get(subscription_id, {})
        logins = sub.get("active_human_logins", 0)
        return {
            "subscription_id": subscription_id,
            "active_sessions": logins,
            "last_login_days_ago": 0 if logins > 0 else 95,
        }

    def check_webhooks(self, subscription_id: str) -> dict:
        sub = SUBSCRIPTIONS.get(subscription_id, {})
        return {
            "subscription_id": subscription_id,
            "has_webhook": sub.get("has_webhook", False),
            "active_webhooks": sub.get("active_webhooks", []),
        }

    def get_user_type(self, subscription_id: str) -> dict:
        sub = SUBSCRIPTIONS.get(subscription_id, {})
        return {
            "subscription_id": subscription_id,
            "user_type": sub.get("user_type", "human"),
            "is_headless_bot": sub.get("is_headless_bot", False),
        }

    def get_all_subscriptions(self) -> list[dict]:
        """Return the full mock subscription portfolio for the dashboard."""
        result = []
        for sub_id, data in SUBSCRIPTIONS.items():
            result.append({
                "subscription_id": sub_id,
                "vendor": data["vendor"],
                "monthly_cost_usd": data["monthly_cost_usd"],
                "seat_count": data["seat_count"],
                "active_human_logins_last_90d": data["active_human_logins"],
                "is_headless_service_account": data["is_headless_bot"],
                "has_webhook_dependency": data["has_webhook"],
                "auto_renewal_date": data["auto_renewal_date"],
                "cancellation_notice_window_days": data["notice_window_days"],
                "early_termination_fee_usd": data["early_termination_fee"],
                "contract_term_months": data["contract_term_months"],
                "months_remaining": data["months_remaining"],
                "governing_cancellation_clause": data["clause"],
            })
        return result
