"""
SubZero — Modal Digital Twin Sandbox
======================================
Deploys an ephemeral, isolated Modal serverless function that simulates
a real enterprise environment (Okta IDP + GitHub webhooks + software metadata).

Deploy with:
    modal deploy sandbox/modal_twin.py

The deployed endpoint URL → set as MODAL_SANDBOX_URL in your .env.
"""

import sys
import os
# Allow importing mock_enterprise from the sandbox directory
sys.path.insert(0, os.path.dirname(__file__))

import modal
from mock_enterprise import MockEnterpriseEnv
import hashlib
import json
from datetime import datetime

# ── Modal App Definition ───────────────────────────────────────────────────────
app = modal.App("subzero-digital-twin")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("fastapi", "pydantic")
)


@app.function(image=image, timeout=120)
@modal.web_endpoint(method="POST")
def simulate(payload: dict) -> dict:
    """
    Receives a simulation request:
      { subscription_id, vendor_name, action }
    Runs a dry-run deprovisioning in an isolated ephemeral environment.
    Returns a SimulationResult dict.
    """
    subscription_id = payload.get("subscription_id", "")
    vendor_name     = payload.get("vendor_name", "")
    action          = payload.get("action", "CANCEL")

    env = MockEnterpriseEnv()
    steps = []
    broken = []

    # ── Step 1: Okta IDP Session Check ────────────────────────────────────────
    steps.append(f"[1] Querying Okta IDP for active sessions on {subscription_id}...")
    idp = env.check_idp_sessions(subscription_id)
    steps.append(f"    → active_sessions: {idp['active_sessions']} | last_login_days_ago: {idp['last_login_days_ago']}")

    # ── Step 2: GitHub / Webhook Dependency Check ─────────────────────────────
    steps.append(f"[2] Scanning GitHub Actions & webhook registry for {subscription_id}...")
    hooks = env.check_webhooks(subscription_id)
    if hooks["active_webhooks"]:
        broken.extend(hooks["active_webhooks"])
        steps.append(f"    → ⚠️  Active webhooks: {hooks['active_webhooks']}")
    else:
        steps.append("    → No active webhooks detected.")

    # ── Step 3: Software Metadata / user_type Check ────────────────────────────
    steps.append(f"[3] Querying software metadata registry for {subscription_id}...")
    meta = env.get_user_type(subscription_id)
    steps.append(f"    → user_type: {meta['user_type']} | is_headless_bot: {meta['is_headless_bot']}")
    if meta["is_headless_bot"]:
        broken.append(f"headless_service_account")
        steps.append("    → 🚨 TRAP: This is a headless CI/CD service account. Cancellation aborted.")

    # ── Step 4: Determine Outcome ──────────────────────────────────────────────
    if broken:
        return {
            "subscription_id": subscription_id,
            "action": action,
            "status": "FAULT",
            "safety_proof_hash": None,
            "fault_reason": f"Cancellation blocked: {', '.join(broken)}",
            "broken_services": broken,
            "steps_executed": steps,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    # ── All Clear: Generate cryptographic safety proof ────────────────────────
    state = json.dumps({
        "subscription_id": subscription_id,
        "action": action,
        "idp": idp,
        "webhooks": hooks,
        "meta": meta,
    }, sort_keys=True)
    proof = hashlib.sha256(state.encode()).hexdigest()
    steps.append(f"[4] ✅ Safety proof generated: {proof[:16]}...")

    return {
        "subscription_id": subscription_id,
        "action": action,
        "status": "SAFE",
        "safety_proof_hash": proof,
        "fault_reason": None,
        "broken_services": [],
        "steps_executed": steps,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
