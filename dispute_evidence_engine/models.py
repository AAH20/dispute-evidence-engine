"""
Data models for dispute-evidence-engine.
Defines Visa CE 3.0 compelling evidence entities, historical orders, and carrier telematics.
Uses pure standard library dataclasses for zero-dependency portability.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
import time
import hashlib

class CardScheme(str, Enum):
    VISA = "VISA"
    MASTERCARD = "MASTERCARD"
    AMERICAN_EXPRESS = "AMERICAN_EXPRESS"
    MEEZA = "MEEZA"

class DisputeReasonCode(str, Enum):
    VISA_10_4_FRAUD_CARD_ABSENT = "10.4"
    VISA_13_1_NOT_RECEIVED = "13.1"
    MC_4837_NO_CARDHOLDER_AUTH = "4837"
    MC_4853_GOODS_SERVICES_DISPUTE = "4853"

@dataclass
class HistoricalOrder:
    order_id: str
    customer_id: str
    amount: float
    ip_address: str
    device_fingerprint: str
    shipping_address: str
    timestamp: float
    undisputed: bool = True
    transaction_identifier: str = ""

@dataclass
class CarrierDeliveryTelematics:
    tracking_number: str
    carrier: str  # "FEDEX", "UPS", "DHL", "ARAMEX"
    recipient_name: str
    delivery_timestamp: float
    gps_coordinates: str  # "lat,lon"
    signature_base64: Optional[str] = None
    delivered_to_address: str = ""

@dataclass
class DisputeCase:
    dispute_id: str
    scheme: CardScheme
    reason_code: DisputeReasonCode
    disputed_amount: float
    order_id: str
    acquirer_reference_number: str  # ARN
    currency: str = "USD"
    filed_timestamp: float = field(default_factory=time.time)
    sla_deadline_timestamp: float = field(default_factory=lambda: time.time() + (14 * 86400))

@dataclass
class CompellingEvidencePackage:
    package_id: str
    dispute_id: str
    scheme: CardScheme
    qualifying_orders: List[HistoricalOrder]
    carrier_telematics: Optional[CarrierDeliveryTelematics]
    matching_dimensions: List[str]  # e.g., ["IP_MATCH", "DEVICE_MATCH", "ADDRESS_MATCH"]
    ce3_compliant: bool
    win_probability_score: float  # 0.00 to 1.00
    generated_at: float = field(default_factory=time.time)

    def compute_sha256_hash(self) -> str:
        order_ids = ",".join(o.order_id for o in self.qualifying_orders)
        payload = f"{self.package_id}:{self.dispute_id}:{order_ids}:{self.ce3_compliant}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

@dataclass
class NetworkSubmissionReceipt:
    submission_id: str
    dispute_id: str
    network_channel: str  # "VROL_DIRECT" or "MCN_ETHOCA"
    network_ack_code: str
    status: str  # "ACCEPTED_FOR_ARBITRATION"
    a2zsoc_seal: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
