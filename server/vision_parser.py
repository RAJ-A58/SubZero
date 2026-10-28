"""
SubZero — Visual-Legal Document Parser
=======================================
Pipeline:
  1. If PDF: convert pages to images using PyPDF / Pillow
  2. For each page image → SAM 3.1 (Meta Model API) to segment visual regions
     (fee tables, riders, signature blocks, fine-print columns)
  3. Cropped high-resolution segments → Muse Wonder (multimodal LLM) to extract
     structured contract fields
  4. Merge fields across pages → return final ContractModel
"""

import os
import io
import base64
import json
import httpx
from PIL import Image
from pypdf import PdfReader
from pydantic import BaseModel
from typing import Optional


# ── Data Models ───────────────────────────────────────────────────────────────
class ContractModel(BaseModel):
    vendor_name: str
    contract_id: Optional[str] = None
    monthly_cost_usd: Optional[float] = None
    seat_count: Optional[int] = None
    auto_renewal_date: Optional[str] = None          # ISO 8601 date string
    cancellation_notice_window_days: Optional[int] = None
    early_termination_fee_usd: Optional[float] = None
    contract_term_months: Optional[int] = None
    governing_cancellation_clause: Optional[str] = None
    raw_extracted_text: Optional[str] = None
    confidence_score: Optional[float] = None


# ── ContractParser ─────────────────────────────────────────────────────────────
class ContractParser:
    """Orchestrates SAM 3.1 segmentation + Muse Wonder extraction."""

    META_API_BASE = os.getenv("META_API_BASE_URL", "https://api.meta.ai/v1")
    META_API_KEY  = os.getenv("META_API_KEY", "")

    def __init__(self):
        self.http = httpx.AsyncClient(timeout=60.0)

    # ── Public entry point ──────────────────────────────────────────────────
    async def parse(self, file_bytes: bytes, content_type: str) -> dict:
        """
        Accepts raw bytes for a PDF or image contract and returns a
        ContractModel as a dict.
        """
        # Step 1: Extract page images
        page_images = self._extract_pages(file_bytes, content_type)

        all_segments: list[str] = []

        for img in page_images:
            # Step 2: SAM 3.1 — get visual segment crops
            crops = await self._sam_segment(img)
            # Step 3: Muse Wonder — extract text fields from each segment
            for crop in crops:
                text = await self._muse_wonder_extract(crop)
                if text:
                    all_segments.append(text)

        # Step 4: Muse Wonder — synthesize all extracted text into ContractModel
        contract = await self._synthesize(all_segments)
        return contract.model_dump()

    # ── Step 1: PDF → PIL Images ────────────────────────────────────────────
    def _extract_pages(self, file_bytes: bytes, content_type: str) -> list[Image.Image]:
        """Convert PDF pages or raw images into PIL Image objects."""
        if content_type == "application/pdf":
            images = []
            reader = PdfReader(io.BytesIO(file_bytes))
            for page in reader.pages:
                # Render at 200 DPI via page mediabox for high-res crops
                # We create a basic representation from the page dimensions
                width  = int(page.mediabox.width)
                height = int(page.mediabox.height)
                # Create a white placeholder canvas sized to PDF page
                # In production replace with pdf2image/poppler for real rendering
                img = Image.new("RGB", (width, height), color="white")
                images.append(img)
            return images
        else:
            img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
            return [img]

    # ── Step 2: SAM 3.1 Segmentation ────────────────────────────────────────
    async def _sam_segment(self, img: Image.Image) -> list[Image.Image]:
        """
        Send the page image to Meta SAM 3.1 via Meta Model API.
        Returns a list of cropped PIL Images (one per detected segment region).
        Falls back to returning the whole image as a single segment if the API
        is unavailable (useful during local dev without keys).
        """
        try:
            img_b64 = self._pil_to_b64(img)
            payload = {
                "model": "sam-3.1",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"},
                            },
                            {
                                "type": "text",
                                "text": (
                                    "Segment all distinct visual regions in this contract page that contain: "
                                    "pricing tables, fee schedules, auto-renewal clauses, cancellation notices, "
                                    "penalty riders, and fine-print addendums. "
                                    "Return bounding box coordinates [x1, y1, x2, y2] for each region as JSON."
                                ),
                            },
                        ],
                    }
                ],
            }
            response = await self.http.post(
                f"{self.META_API_BASE}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self.META_API_KEY}"},
            )
            response.raise_for_status()
            data = response.json()
            raw = data["choices"][0]["message"]["content"]

            # Parse bounding boxes and crop
            boxes = self._parse_boxes(raw)
            if boxes:
                crops = []
                for box in boxes:
                    x1, y1, x2, y2 = box
                    crops.append(img.crop((x1, y1, x2, y2)))
                return crops

        except Exception as e:
            print(f"[SAM 3.1] Fallback — returning full page. Error: {e}")

        # Fallback: return full page as single "segment"
        return [img]

    # ── Step 3: Muse Wonder Clause Extraction ────────────────────────────────
    async def _muse_wonder_extract(self, crop: Image.Image) -> str:
        """
        Send a segment crop to Muse Wonder. Ask it to extract all relevant
        contract terms as structured JSON text.
        """
        try:
            crop_b64 = self._pil_to_b64(crop)
            payload = {
                "model": "muse-wonder",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{crop_b64}"},
                            },
                            {
                                "type": "text",
                                "text": (
                                    "Extract all relevant contract terms from this image segment. "
                                    "Return a JSON object with keys (use null if not present): "
                                    "vendor_name, contract_id, monthly_cost_usd, seat_count, "
                                    "auto_renewal_date (ISO 8601), cancellation_notice_window_days (integer), "
                                    "early_termination_fee_usd (float), contract_term_months (integer), "
                                    "governing_cancellation_clause (quoted text from document). "
                                    "Return ONLY valid JSON. No prose."
                                ),
                            },
                        ],
                    }
                ],
            }
            response = await self.http.post(
                f"{self.META_API_BASE}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self.META_API_KEY}"},
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]

        except Exception as e:
            print(f"[Muse Wonder] Extraction error: {e}")
            return ""

    # ── Step 4: Synthesise into ContractModel ─────────────────────────────────
    async def _synthesize(self, segments: list[str]) -> ContractModel:
        """
        Merge all extracted text fragments via Muse Wonder into a single
        canonical ContractModel (deduplicating and resolving conflicts).
        """
        combined = "\n\n---\n\n".join(segments) if segments else "No segments extracted."
        try:
            payload = {
                "model": "muse-wonder",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a contract intelligence engine. You receive multiple JSON fragments "
                            "extracted from different visual regions of a single enterprise contract. "
                            "Merge them into ONE canonical JSON object, resolving conflicts by preferring "
                            "the most specific / non-null value. Return ONLY valid JSON, no prose."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Merge these contract fragments:\n\n{combined}",
                    },
                ],
            }
            response = await self.http.post(
                f"{self.META_API_BASE}/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {self.META_API_KEY}"},
            )
            response.raise_for_status()
            raw = response.json()["choices"][0]["message"]["content"]
            parsed = json.loads(raw)
            return ContractModel(**parsed)

        except Exception as e:
            print(f"[Synthesise] Error: {e}")
            # Return a best-effort empty model so the API doesn't crash
            return ContractModel(vendor_name="Unknown", confidence_score=0.0)

    # ── Utilities ─────────────────────────────────────────────────────────────
    @staticmethod
    def _pil_to_b64(img: Image.Image) -> str:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        return base64.b64encode(buf.getvalue()).decode()

    @staticmethod
    def _parse_boxes(raw: str) -> list[list[int]]:
        """Best-effort parse of bounding boxes from SAM 3.1 response."""
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return [[int(v) for v in b] for b in data]
            if isinstance(data, dict) and "boxes" in data:
                return [[int(v) for v in b] for b in data["boxes"]]
        except Exception:
            pass
        return []
