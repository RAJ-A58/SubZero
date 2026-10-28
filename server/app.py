"""
SubZero — FastAPI Application Entry Point
=========================================
Routes:
  POST /api/analyze-contract   → Vision-Legal Document Parser (SAM 3.1 + Muse Wonder)
  POST /api/decide             → Policy & Payoff Engine     (Muse Spark Open on Baseten)
  POST /api/simulate           → Digital Twin Sandbox       (Modal)
  POST /api/voice-approve      → Voice Authorization        (Muse Voice Transcribe)
  POST /api/generate-notice    → Legal Notice Generator     (Muse Spark Open)
  GET  /api/health             → Health check
"""

import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

from vision_parser import ContractParser
from decision_engine import DecisionEngine, DecisionRequest
from sandbox_client import SandboxClient
from voice_handler import VoiceHandler
from legal_generator import LegalNoticeGenerator

load_dotenv()

app = FastAPI(
    title="SubZero — VeriDeprovision API",
    description="Verifiable Autonomous SaaS Deprovisioning & Contract Renegotiation Engine",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Initialise service singletons ──────────────────────────────────────────────
contract_parser  = ContractParser()
decision_engine  = DecisionEngine()
sandbox_client   = SandboxClient()
voice_handler    = VoiceHandler()
legal_generator  = LegalNoticeGenerator()


# ── Health ─────────────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "SubZero VeriDeprovision API"}


# ── 1. Analyse Contract (SAM 3.1 + Muse Wonder) ──────────────────────────────
@app.post("/api/analyze-contract")
async def analyze_contract(file: UploadFile = File(...)):
    """
    Accept a contract PDF or image.
    Returns structured fields: notice_window_days, renewal_date,
    early_termination_fee, seat_count, monthly_cost, vendor_name.
    """
    if file.content_type not in ("application/pdf", "image/png", "image/jpeg"):
        raise HTTPException(status_code=415, detail="Unsupported file type. Send PDF, PNG, or JPEG.")

    contents = await file.read()
    result = await contract_parser.parse(file_bytes=contents, content_type=file.content_type)
    return result


# ── 2. Policy & Payoff Decision (Muse Spark Open on Baseten) ─────────────────
@app.post("/api/decide")
async def decide(request: DecisionRequest):
    """
    Given structured contract data + IDP usage data, return a deterministic
    decision: IMMEDIATE_CANCEL | DOWNGRADE_TIER | SCHEDULE_NOTICE | RENEGOTIATE | PROTECT
    along with a full chain-of-verification reasoning trace.
    """
    result = await decision_engine.evaluate(request)
    return result


# ── 3. Digital Twin Simulation (Modal Sandbox) ───────────────────────────────
class SimulationRequest(BaseModel):
    subscription_id: str
    vendor_name: str
    action: str  # "CANCEL" | "DOWNGRADE" | "REASSIGN"


@app.post("/api/simulate")
async def simulate(request: SimulationRequest):
    """
    Spawns an ephemeral Modal sandbox replicating Okta IDP + GitHub webhooks.
    Dry-runs the proposed action. Returns Safety Proof (hash) if safe, or
    a Fault Report identifying what would break.
    """
    result = await sandbox_client.run_simulation(
        subscription_id=request.subscription_id,
        vendor_name=request.vendor_name,
        action=request.action,
    )
    return result


# ── 4. Voice Authorization (Muse Voice Transcribe) ───────────────────────────
@app.post("/api/voice-approve")
async def voice_approve(audio: UploadFile = File(...)):
    """
    Accept an audio file from the executive dashboard.
    Transcribes and extracts intent + authorization from the audio using
    Meta Muse Voice Transcribe. Returns parsed approval commands.
    """
    if audio.content_type not in ("audio/wav", "audio/mpeg", "audio/webm"):
        raise HTTPException(status_code=415, detail="Unsupported audio type. Send WAV, MP3, or WEBM.")

    audio_bytes = await audio.read()
    result = await voice_handler.process(audio_bytes=audio_bytes, content_type=audio.content_type)
    return result


# ── 5. Legal Notice Generator (Muse Spark Open) ──────────────────────────────
class NoticeRequest(BaseModel):
    vendor_name: str
    contract_id: str
    cancellation_clause: str
    effective_date: str
    company_name: str
    signatory_name: str
    signatory_title: str


@app.post("/api/generate-notice")
async def generate_notice(request: NoticeRequest):
    """
    Generates a formal, legally binding vendor termination or downgrade notice
    letter, citing exact MSA clause, contract ID, and effective date.
    """
    result = await legal_generator.generate(request)
    return result
