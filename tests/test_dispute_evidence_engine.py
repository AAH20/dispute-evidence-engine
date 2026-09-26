"""
Unit tests for dispute-evidence-engine.
Verifies Visa CE 3.0 matching logic, synthesis of evidence packets, network dispatch, and a2zsoc seals.
"""

import unittest
import time
from dispute_evidence_engine.models import (
    CardScheme,
    DisputeReasonCode,
    DisputeCase,
    HistoricalOrder,
    CarrierDeliveryTelematics,
)
from dispute_evidence_engine.ce3_qualifying_matcher import CE3QualifyingMatcher
from dispute_evidence_engine.compelling_evidence_synthesizer import CompellingEvidenceSynthesizer
from dispute_evidence_engine.vrol_mcn_api_dispatcher import NetworkAPIDispatcher
from dispute_evidence_engine.a2zsoc_dispute_vault_bridge import A2ZSOCDisputeBridge

class TestDisputeEvidenceEngine(unittest.TestCase):
    def setUp(self):
        self.matcher = CE3QualifyingMatcher()
        self.synth = CompellingEvidenceSynthesizer()
        self.dispatcher = NetworkAPIDispatcher()
        self.bridge = A2ZSOCDisputeBridge()

    def test_ce3_matching_success(self):
        now = time.time()
        dispute = DisputeCase(
            dispute_id="dsp_001",
            scheme=CardScheme.VISA,
            reason_code=DisputeReasonCode.VISA_10_4_FRAUD_CARD_ABSENT,
            disputed_amount=500.0,
            order_id="ord_current",
            acquirer_reference_number="arn_test_1"
        )
        current_order = HistoricalOrder(
            order_id="ord_current",
            customer_id="c_1",
            amount=500.0,
            ip_address="1.2.3.4",
            device_fingerprint="fp_123",
            shipping_address="123 Main St",
            timestamp=now
        )
        history = [
            HistoricalOrder(
                order_id="ord_prev_1",
                customer_id="c_1",
                amount=100.0,
                ip_address="1.2.3.4",
                device_fingerprint="fp_123",
                shipping_address="123 Main St",
                timestamp=now - (130 * 86400),
                undisputed=True
            ),
            HistoricalOrder(
                order_id="ord_prev_2",
                customer_id="c_1",
                amount=150.0,
                ip_address="1.2.3.4",
                device_fingerprint="fp_123",
                shipping_address="123 Main St",
                timestamp=now - (200 * 86400),
                undisputed=True
            )
        ]

        is_compliant, qualifying, dimensions = self.matcher.match_qualifying_orders(
            dispute, current_order, history
        )
        self.assertTrue(is_compliant)
        self.assertEqual(len(qualifying), 2)
        self.assertIn("IP_ADDRESS_MATCH", dimensions)
        self.assertIn("DEVICE_FINGERPRINT_MATCH", dimensions)

    def test_ce3_matching_insufficient_prior_orders(self):
        now = time.time()
        dispute = DisputeCase(
            dispute_id="dsp_002",
            scheme=CardScheme.VISA,
            reason_code=DisputeReasonCode.VISA_10_4_FRAUD_CARD_ABSENT,
            disputed_amount=200.0,
            order_id="ord_c2",
            acquirer_reference_number="arn_test_2"
        )
        current_order = HistoricalOrder(
            order_id="ord_c2",
            customer_id="c_2",
            amount=200.0,
            ip_address="9.9.9.9",
            device_fingerprint="fp_999",
            shipping_address="456 Elm St",
            timestamp=now
        )
        history = [
            HistoricalOrder(
                order_id="ord_single",
                customer_id="c_2",
                amount=50.0,
                ip_address="9.9.9.9",
                device_fingerprint="fp_999",
                shipping_address="456 Elm St",
                timestamp=now - (150 * 86400),
                undisputed=True
            )
        ]

        is_compliant, qualifying, dimensions = self.matcher.match_qualifying_orders(
            dispute, current_order, history
        )
        # Visa CE 3.0 requires >= 2 qualifying orders
        self.assertFalse(is_compliant)
        self.assertEqual(len(qualifying), 1)

    def test_evidence_synthesis_and_dispatch(self):
        dispute = DisputeCase(
            dispute_id="dsp_003",
            scheme=CardScheme.VISA,
            reason_code=DisputeReasonCode.VISA_10_4_FRAUD_CARD_ABSENT,
            disputed_amount=1200.0,
            order_id="ord_c3",
            acquirer_reference_number="arn_test_3"
        )
        orders = [
            HistoricalOrder(order_id="o1", customer_id="c3", amount=100.0, ip_address="a", device_fingerprint="b", shipping_address="c", timestamp=10.0),
            HistoricalOrder(order_id="o2", customer_id="c3", amount=120.0, ip_address="a", device_fingerprint="b", shipping_address="c", timestamp=20.0)
        ]
        telematics = CarrierDeliveryTelematics(
            tracking_number="TRACK_123",
            carrier="UPS",
            recipient_name="Recipient",
            delivery_timestamp=time.time(),
            gps_coordinates="10.0,20.0",
            signature_base64="sig_mock"
        )

        package = self.synth.synthesize_package(
            dispute, orders, ["IP_ADDRESS_MATCH", "DEVICE_FINGERPRINT_MATCH"], telematics
        )
        self.assertTrue(package.ce3_compliant)
        self.assertGreater(package.win_probability_score, 0.70)

        receipt = self.dispatcher.dispatch_to_network(package)
        self.assertEqual(receipt.network_channel, "VROL_DIRECT_API")
        self.assertEqual(receipt.status, "ACCEPTED_FOR_ARBITRATION")

        seal = self.bridge.anchor_dispute_evidence(package, receipt)
        self.assertTrue(seal.startswith("a2z_dispute_seal_"))

if __name__ == "__main__":
    unittest.main()
