"""
SubZero — Voice Authorization Handler
=======================================
Uses Meta Muse Voice Transcribe to:
  1. Accept executive audio commands from the dashboard
  2. Transcribe the speech to text
  3. Extract structured authorization commands:
     - approved_subscriptions: list of subscription IDs approved for action
     - denied_subscriptions: list of IDs explicitly held back
     - global_approval: true if exec says "approve all" / "proceed"
     - detected_intent: the full transcription + extracted intent
"""

import os
import io
import base64
import json
import httpx
from pydantic import BaseModel
from typing import Optional


class VoiceAuthResult(BaseModel):
    transcription: str
    approved_subscriptions: list[str]
    denied_subscriptions: list[str]
    global_approval: bool
    raw_intent: Optional[str] = None
    confidence: float


class VoiceHandler:
    """Processes executive audio via Meta Muse Voice Transcribe API."""

    META_API_BASE = os.getenv("META_API_BASE_URL", "https://api.meta.ai/v1")
    META_API_KEY  = os.getenv("META_API_KEY", "")

    def __init__(self):
        self.http = httpx.AsyncClient(timeout=60.0)

    async def process(self, audio_bytes: bytes, content_type: str) -> dict:
        # Step 1: Transcribe audio using Muse Voice Transcribe
        transcription = await self._transcribe(audio_bytes, content_type)

        # Step 2: Extract authorization intents using Muse Spark Open
        intent = await self._extract_intent(transcription)

        return VoiceAuthResult(
            transcription=transcription,
            approved_subscriptions=intent.get("approved_subscriptions", []),
            denied_subscriptions=intent.get("denied_subscriptions", []),
            global_approval=intent.get("global_approval", False),
            raw_intent=json.dumps(intent),
            confidence=intent.get("confidence", 0.85),
        ).model_dump()

    # ── Step 1: Muse Voice Transcribe ─────────────────────────────────────────
    async def _transcribe(self, audio_bytes: bytes, content_type: str) -> str:
        try:
            audio_b64 = base64.b64encode(audio_bytes).decode()
            payload = {
                "model": "muse-voice-transcribe",
                "audio": {
                    "data": audio_b64,
                    "format": content_type.split("/")[-1],  # "wav", "mpeg", "webm"
                },
                "language": "en",
            }
            response = await self.http.post(
                f"{self.META_API_BASE}/audio/transcriptions",
                json=payload,
                headers={"Authorization": f"Bearer {self.META_API_KEY}"},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("text", "")

        except Exception as e:
            print(f"[Muse Voice Transcribe] Error: {e}")
            return ""

    # ── Step 2: Intent Extraction (Muse Spark Open) ───────────────────────────
    async def _extract_intent(self, transcription: str) -> dict:
        if not transcription:
            return {
                "approved_subscriptions": [],
                "denied_subscriptions": [],
                "global_approval": False,
                "confidence": 0.0,
            }

        system_prompt = (
            "You are SubZero's voice authorization parser. "
            "Given an executive's speech transcription about approving or rejecting "
            "SaaS subscription cancellations, extract a structured JSON object with keys: "
            "approved_subscriptions (list of subscription IDs or vendor names approved), "
            "denied_subscriptions (list of IDs or vendor names explicitly held back), "
            "global_approval (boolean: true if exec approves ALL pending actions), "
            "confidence (float 0.0-1.0). "
            "Return ONLY valid JSON. No prose."
        )

        baseten_key  = os.getenv("BASETEN_API_KEY", "")
        baseten_base = os.getenv("BASETEN_API_BASE", "https://api.baseten.co/v1")
        model_id     = os.getenv("BASETEN_MODEL_ID", "meta-models/muse-spark-open-1026")

        try:
            response = await self.http.post(
                f"{baseten_base}/chat/completions",
                json={
                    "model": model_id,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": f'Transcription: "{transcription}"'},
                    ],
                    "max_tokens": 256,
                    "temperature": 0.0,
                },
                headers={
                    "Authorization": f"Api-Key {baseten_key}",
                    "Content-Type":  "application/json",
                },
            )
            response.raise_for_status()
            raw = response.json()["choices"][0]["message"]["content"]
            return json.loads(raw)

        except Exception as e:
            print(f"[Intent Extraction] Error: {e}")
            return {
                "approved_subscriptions": [],
                "denied_subscriptions": [],
                "global_approval": False,
                "confidence": 0.5,
            }
