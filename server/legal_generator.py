"""
SubZero — Legal Notice Generator
==================================
Generates formal, legally binding vendor termination or downgrade notices
using Muse Spark Open on Baseten. The letter cites the exact MSA clause,
contract ID, and statutory effective date.
"""

import os
import json
import httpx
from datetime import date, datetime, timedelta
from pydantic import BaseModel
from typing import Optional


class LegalNotice(BaseModel):
    vendor_name: str
    contract_id: str
    letter_body: str
    effective_date: str
    generated_at: str


class LegalNoticeGenerator:
    """Generates iron-clad termination / downgrade notices via Muse Spark Open."""

    BASETEN_API_KEY  = os.getenv("BASETEN_API_KEY", "")
    BASETEN_MODEL_ID = os.getenv("BASETEN_MODEL_ID", "meta-models/muse-spark-open-1026")
    BASETEN_API_BASE = os.getenv("BASETEN_API_BASE", "https://api.baseten.co/v1")

    def __init__(self):
        self.http = httpx.AsyncClient(timeout=90.0)

    async def generate(self, req) -> dict:
        letter = await self._generate_letter(req)
        return LegalNotice(
            vendor_name=req.vendor_name,
            contract_id=req.contract_id,
            letter_body=letter,
            effective_date=req.effective_date,
            generated_at=datetime.utcnow().isoformat() + "Z",
        ).model_dump()

    async def _generate_letter(self, req) -> str:
        system_prompt = (
            "You are a senior enterprise legal counsel specialising in SaaS contract terminations. "
            "Generate a formal, professional vendor termination notice letter. "
            "Requirements:\n"
            "  - Cite the exact contract clause provided\n"
            "  - Include the Contract ID prominently in the subject line\n"
            "  - State the effective date of termination clearly\n"
            "  - Use formal business letter format\n"
            "  - Keep it concise (max 300 words)\n"
            "  - Do NOT include placeholder text like [YOUR NAME] — use the provided details\n"
            "  - End with a request for written confirmation of receipt"
        )

        user_message = (
            f"Generate a vendor termination notice with these details:\n"
            f"  Vendor Name: {req.vendor_name}\n"
            f"  Contract ID: {req.contract_id}\n"
            f"  Effective Termination Date: {req.effective_date}\n"
            f"  Governing Cancellation Clause: \"{req.cancellation_clause}\"\n"
            f"  Sending Company: {req.company_name}\n"
            f"  Signatory Name: {req.signatory_name}\n"
            f"  Signatory Title: {req.signatory_title}\n"
            f"  Letter Date: {date.today().strftime('%B %d, %Y')}"
        )

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
                    "temperature": 0.3,
                },
                headers={
                    "Authorization": f"Api-Key {self.BASETEN_API_KEY}",
                    "Content-Type":  "application/json",
                },
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

        except Exception as e:
            print(f"[Legal Generator] Error: {e}")
            # Fallback: deterministic letter template
            return (
                f"NOTICE OF CONTRACT TERMINATION\n"
                f"Contract ID: {req.contract_id}\n"
                f"Date: {date.today().strftime('%B %d, %Y')}\n\n"
                f"Dear {req.vendor_name} Account Management Team,\n\n"
                f"This letter constitutes formal written notice of termination of our subscription "
                f"agreement (Contract ID: {req.contract_id}) pursuant to {req.cancellation_clause}.\n\n"
                f"The effective date of termination is {req.effective_date}.\n\n"
                f"We request written confirmation of receipt and acknowledgement of this termination "
                f"within 5 business days.\n\n"
                f"Sincerely,\n{req.signatory_name}\n{req.signatory_title}\n{req.company_name}"
            )
