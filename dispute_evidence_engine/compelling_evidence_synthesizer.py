"""
Compelling Evidence Package Synthesizer.
Assembles certified defense packets conforming to Visa CE 3.0 and Mastercard First-Party Fraud standards.
"""

from typing import List, Optional
import uuid
import time
from .models import (
    DisputeCase,
    HistoricalOrder,
    CarrierDeliveryTelematics,
    CompellingEvidencePackage,
)

class CompellingEvidenceSynthesizer:
    def synthesize_package(
        self,
        dispute: DisputeCase,
        qualifying_orders: List[HistoricalOrder],
        matching_dimensions: List[str],
        carrier_telematics: Optional[CarrierDeliveryTelematics] = None
    ) -> CompellingEvidencePackage:
        """
        Assembles a cryptographically structured Compelling Evidence package.
        Calculates win probability based on evidentiary strength.
        """
        is_compliant = len(qualifying_orders) >= 2 and len(matching_dimensions) >= 1

        # Win probability scoring model
        score = 0.35  # baseline merchant win-rate
        if is_compliant:
            score += 0.35  # Visa CE 3.0 rule qualification (+35%)
        if "DEVICE_FINGERPRINT_MATCH" in matching_dimensions:
            score += 0.10
        if "SHIPPING_DESTINATION_MATCH" in matching_dimensions:
            score += 0.08
        if carrier_telematics and carrier_telematics.signature_base64:
            score += 0.07  # Carrier signature proof (+7%)

        score = min(0.98, score)

        return CompellingEvidencePackage(
            package_id=f"ce3_pkg_{uuid.uuid4().hex[:12]}",
            dispute_id=dispute.dispute_id,
            scheme=dispute.scheme,
            qualifying_orders=qualifying_orders,
            carrier_telematics=carrier_telematics,
            matching_dimensions=matching_dimensions,
            ce3_compliant=is_compliant,
            win_probability_score=round(score, 3),
            generated_at=time.time()
        )
