"""
SubZero — Digital Twin Sandbox Client
=======================================
Talks to the Modal sandbox defined in sandbox/modal_twin.py.
In local dev mode, falls back to the pure-Python mock enterprise environment
in sandbox/mock_enterprise.py so you can test without GPU credits.
"""

import os
import hashlib
import json
import httpx
from datetime import datetime
from pydantic import BaseModel
from typing import Literal, Optional


SimulationStatus = Literal["SAFE", "FAULT"]


class SimulationResult(BaseModel):
    subscription_id: str
    action: str
    status: SimulationStatus
    safety_proof_hash: Optional[str] = None   # SHA-256 of the safe execution state
    fault_reason: Optional[str] = None
    broken_services: list[str] = []
    steps_executed: list[str] = []
    timestamp: str


class SandboxClient:
    """
    Sends simulation requests to the Modal ephemeral sandbox endpoint.
    Falls back to local mock simulation if MODAL_SANDBOX_URL is not set.
    """

    MODAL_SANDBOX_URL = os.getenv("MODAL_SANDBOX_URL", "")  # Set after `modal deploy`

    def __init__(self):
        self.http = httpx.AsyncClient(timeout=120.0)

    async def run_simulation(
        self,
        subscription_id: str,
        vendor_name: str,
        action: str,
    ) -> dict:
        if self.MODAL_SANDBOX_URL:
            return await self._remote_simulation(subscription_id, vendor_name, action)
        else:
            return await self._local_simulation(subscription_id, vendor_name, action)

    # ── Remote Modal Sandbox ──────────────────────────────────────────────────
    async def _remote_simulation(self, subscription_id: str, vendor_name: str, action: str) -> dict:
        try:
            response = await self.http.post(
                self.MODAL_SANDBOX_URL,
                json={
                    "subscription_id": subscription_id,
                    "vendor_name": vendor_name,
                    "action": action,
                },
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[Modal Sandbox] Remote call failed, falling back to local: {e}")
            return await self._local_simulation(subscription_id, vendor_name, action)

    # ── Local Mock Simulation (Offline Dev) ────────────────────────────────────
    async def _local_simulation(self, subscription_id: str, vendor_name: str, action: str) -> dict:
        """
        Pure-Python digital-twin simulation.
        Imports the mock enterprise environment and dry-runs the action,
        checking for broken webhooks, headless bot dependencies, and active SSO tokens.
        """
        from mock_enterprise import MockEnterpriseEnv

        env = MockEnterpriseEnv()
        steps = []
        broken = []

        # Step 1: Check Okta IDP for active SSO sessions
        steps.append(f"[1] Checking Okta IDP for active SSO sessions on {subscription_id}...")
        idp_result = env.check_idp_sessions(subscription_id)
        if idp_result["active_sessions"] > 0:
            steps.append(f"    → {idp_result['active_sessions']} active SSO sessions found.")
        else:
            steps.append("    → No active SSO sessions.")

        # Step 2: Check GitHub/CI webhook tokens bound to this subscription
        steps.append(f"[2] Scanning GitHub Actions & webhooks for tokens tied to {subscription_id}...")
        webhook_result = env.check_webhooks(subscription_id)
        if webhook_result["active_webhooks"]:
            broken.extend(webhook_result["active_webhooks"])
            steps.append(f"    → ⚠️  Active webhooks detected: {webhook_result['active_webhooks']}")
        else:
            steps.append("    → No active webhooks detected.")

        # Step 3: Check if the account is a headless service account
        steps.append(f"[3] Querying user_type for {subscription_id}...")
        user_meta = env.get_user_type(subscription_id)
        steps.append(f"    → user_type: {user_meta['user_type']}")
        if user_meta["user_type"] in ("bot", "service_account"):
            broken.append(f"headless_{user_meta['user_type']}")
            steps.append("    → ⚠️  Service account detected! Cancellation would break automated pipelines.")

        # ── Determine outcome ────────────────────────────────────────────────
        if broken:
            result = SimulationResult(
                subscription_id=subscription_id,
                action=action,
                status="FAULT",
                fault_reason=f"Cancellation blocked: {', '.join(broken)}",
                broken_services=broken,
                steps_executed=steps,
                timestamp=datetime.utcnow().isoformat() + "Z",
            )
        else:
            # Produce a cryptographic safety proof hash
            state_str = json.dumps({
                "subscription_id": subscription_id,
                "action": action,
                "idp": idp_result,
                "webhooks": webhook_result,
                "user_type": user_meta,
            }, sort_keys=True)
            proof = hashlib.sha256(state_str.encode()).hexdigest()
            steps.append(f"[4] Safety proof generated: {proof[:16]}...")
            result = SimulationResult(
                subscription_id=subscription_id,
                action=action,
                status="SAFE",
                safety_proof_hash=proof,
                broken_services=[],
                steps_executed=steps,
                timestamp=datetime.utcnow().isoformat() + "Z",
            )

        return result.model_dump()
