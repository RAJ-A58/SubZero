# -*- coding: utf-8 -*-
"""
SubZero — Local End-to-End Test Runner
=======================================
Tests the full pipeline without any API keys, using deterministic fallbacks.
Run with:
    python test_local.py

Expected output:
    ✅  sw_101 → IMMEDIATE_CANCEL   (safe zombie license)
    ✅  sw_204 → PROTECT            (headless CI/CD bot trapped)
    ✅  sw_307 → SCHEDULE_NOTICE    (ETF penalty avoided)
    ✅  sw_412 → DOWNGRADE_TIER     (partial usage detected)
"""

import asyncio
import sys
import os
import io

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Prevent httpx IllegalHeader crash when keys are not set yet
os.environ.setdefault("BASETEN_API_KEY", "local-test-no-key")
os.environ.setdefault("META_API_KEY",    "local-test-no-key")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "server"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "sandbox"))

from decision_engine import DecisionEngine, DecisionRequest
from sandbox_client import SandboxClient
from mock_enterprise import MockEnterpriseEnv, SUBSCRIPTIONS


EXPECTED = {
    "sw_101": "IMMEDIATE_CANCEL",
    "sw_204": "PROTECT",
    "sw_307": "SCHEDULE_NOTICE",
    "sw_412": "DOWNGRADE_TIER",
}

PASS = "[PASS]"
FAIL = "[FAIL]"


async def run_tests():
    engine = DecisionEngine()
    sandbox = SandboxClient()

    print("\n" + "=" * 70)
    print("  SubZero -- Local End-to-End Test (No API Keys Required)")
    print("=" * 70 + "\n")

    all_passed = True

    for sub_id, data in SUBSCRIPTIONS.items():
        req = DecisionRequest(
            subscription_id                 = sub_id,
            vendor_name                     = data["vendor"],
            monthly_cost_usd                = data["monthly_cost_usd"],
            seat_count                      = data["seat_count"],
            active_human_logins_last_90d    = data["active_human_logins"],
            has_webhook_dependency          = data["has_webhook"],
            is_headless_service_account     = data["is_headless_bot"],
            auto_renewal_date               = data["auto_renewal_date"],
            cancellation_notice_window_days = data["notice_window_days"],
            early_termination_fee_usd       = data["early_termination_fee"],
            contract_term_months            = data["contract_term_months"],
            months_remaining                = data["months_remaining"],
        )

        # Decision Engine
        decision = await engine.evaluate(req)
        action   = decision["action"]
        expected = EXPECTED[sub_id]
        passed   = action == expected

        if not passed:
            all_passed = False

        icon = PASS if passed else FAIL
        trap = ""
        if data["is_headless_bot"]:
            trap = "  [TRAP A: headless bot]"
        elif data["early_termination_fee"] > 0:
            trap = "  [TRAP B: ETF ${:,.0f}]".format(data["early_termination_fee"])

        print("{}  {} ({:8s}) -> {:20s} (expected: {}){}".format(
            icon, sub_id, data["vendor"], action, expected, trap))

        if decision.get("alert_message"):
            print("    ALERT: {}".format(decision["alert_message"]))

        if decision.get("notice_deadline"):
            print("    Notice deadline: {}".format(decision["notice_deadline"]))

        print("    Net savings: ${:,.2f}".format(decision.get("net_savings_usd", 0)))

        # Simulation
        sim = await sandbox.run_simulation(sub_id, data["vendor"], action)
        sim_label = "[SAFE]" if sim["status"] == "SAFE" else "[FAULT]"
        print("    Simulation: {}".format(sim_label), end="")
        if sim.get("safety_proof_hash"):
            print("  |  proof: {}...".format(sim["safety_proof_hash"][:16]))
        elif sim.get("fault_reason"):
            print("\n    BLOCKED: {}".format(sim["fault_reason"]))
        else:
            print()

        print()

    print("=" * 70)
    if all_passed:
        print("  ALL TESTS PASSED -- SubZero pipeline is working correctly!")
    else:
        print("  SOME TESTS FAILED -- check output above.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(run_tests())
