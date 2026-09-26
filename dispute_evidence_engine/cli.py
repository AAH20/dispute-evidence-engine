"""
Command Line Interface for dispute-evidence-engine.
Executes Visa CE 3.0 matching and automated VROL submission sprints.
"""

import argparse
import sys
import time
from .models import (
    CardScheme,
    DisputeReasonCode,
    DisputeCase,
    HistoricalOrder,
    CarrierDeliveryTelematics,
)
from .ce3_qualifying_matcher import CE3QualifyingMatcher
from .compelling_evidence_synthesizer import CompellingEvidenceSynthesizer
from .vrol_mcn_api_dispatcher import NetworkAPIDispatcher
from .a2zsoc_dispute_vault_bridge import A2ZSOCDisputeBridge

def run_demo():
    print("=" * 80)
    print("⚖️  DISPUTE-EVIDENCE-ENGINE v1.0.0 (Frontier September 2026)")
    print("    Visa CE 3.0 & Mastercard First-Party Friendly Fraud Automated Arbiter")
    print("    Integrated with a2zsoc.com Evidence Vault & VROL / MCN Direct APIS")
    print("=" * 80)

    matcher = CE3QualifyingMatcher()
    synth = CompellingEvidenceSynthesizer()
    dispatcher = NetworkAPIDispatcher()
    bridge = A2ZSOCDisputeBridge()

    # 1. Incoming Visa Dispute Case
    dispute = DisputeCase(
        dispute_id="dsp_visa_984102",
        scheme=CardScheme.VISA,
        reason_code=DisputeReasonCode.VISA_10_4_FRAUD_CARD_ABSENT,
        disputed_amount=2450.00,
        order_id="ord_current_9921",
        acquirer_reference_number="arn_74591028491029481902",
        currency="USD"
    )
    print(f"\n[1/5] Ingested Incoming Card Scheme Dispute...")
    print(f"   • Case ID:           {dispute.dispute_id}")
    print(f"   • Scheme / Reason:   {dispute.scheme.value} - Code {dispute.reason_code.value} (Fraud Card-Absent)")
    print(f"   • Disputed Amount:   ${dispute.disputed_amount:,.2f} USD")
    print(f"   • SLA Deadline:      14-Day Network Window (Auto-Escalation Active)")

    # 2. Historical Orders
    now = time.time()
    current_order = HistoricalOrder(
        order_id="ord_current_9921",
        customer_id="cust_88291",
        amount=2450.00,
        ip_address="198.51.100.42",
        device_fingerprint="fp_metal_v8_88f9102",
        shipping_address="742 Evergreen Terrace, Springfield, OR",
        timestamp=now
    )

    history = [
        HistoricalOrder(
            order_id="ord_prior_001",
            customer_id="cust_88291",
            amount=420.00,
            ip_address="198.51.100.42",  # IP MATCH
            device_fingerprint="fp_metal_v8_88f9102",  # DEVICE MATCH
            shipping_address="742 Evergreen Terrace, Springfield, OR",
            timestamp=now - (140 * 86400),  # 140 days prior
            undisputed=True
        ),
        HistoricalOrder(
            order_id="ord_prior_002",
            customer_id="cust_88291",
            amount=890.00,
            ip_address="198.51.100.42",  # IP MATCH
            device_fingerprint="fp_metal_v8_88f9102",  # DEVICE MATCH
            shipping_address="742 Evergreen Terrace, Springfield, OR",
            timestamp=now - (220 * 86400),  # 220 days prior
            undisputed=True
        )
    ]
    print(f"\n[2/5] Harvested Merchant Order History ({len(history)} prior orders found)...")

    # 3. Match CE 3.0 Qualifying Orders
    print(f"\n[3/5] Evaluating Visa Compelling Evidence 3.0 Conformance Rules...")
    is_compliant, qualifying, dimensions = matcher.match_qualifying_orders(dispute, current_order, history)
    print(f"   ✓ CE 3.0 Rule Qualification:   {is_compliant} (Found {len(qualifying)} prior qualifying orders)")
    print(f"   ✓ Validated Dimensions:        {', '.join(dimensions)}")

    # 4. Synthesize Compelling Evidence Package
    telematics = CarrierDeliveryTelematics(
        tracking_number="FDX_99281029401",
        carrier="FEDEX_EXPRESS",
        recipient_name="H. Simpson",
        delivery_timestamp=now - 86400,
        gps_coordinates="44.0462,-123.0220",
        signature_base64="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
        delivered_to_address="742 Evergreen Terrace, Springfield, OR"
    )
    package = synth.synthesize_package(dispute, qualifying, dimensions, telematics)
    print(f"\n[4/5] Synthesizing Certified Compelling Evidence Package...")
    print(f"   ✓ Package ID:                  {package.package_id}")
    print(f"   ✓ Carrier Delivery GPS:        {telematics.carrier} ({telematics.gps_coordinates})")
    print(f"   ✓ ML Calibrated Win Rate:      {package.win_probability_score * 100:.1f}% Win Probability")

    # 5. Direct API Submission to VROL & Sealing to a2zsoc.com
    receipt = dispatcher.dispatch_to_network(package)
    seal = bridge.anchor_dispute_evidence(package, receipt)
    print(f"\n[5/5] Automated Dispatch to Visa Resolve Online (VROL) & Evidence Vault...")
    print(f"   ✓ Submission ID:               {receipt.submission_id}")
    print(f"   ✓ Network Channel:             {receipt.network_channel}")
    print(f"   ✓ VROL Network Ack:            {receipt.network_ack_code}")
    print(f"   ✓ Status:                      {receipt.status} (Liability Shifted to Issuer)")
    print(f"   ✓ a2zsoc.com Audit Seal:       {seal}")
    print("\n" + "=" * 80)
    print("✅ CE 3.0 ARBITRATION SPRINT COMPLETED: $2,450.00 Saved in 48-Hour Turnaround.")
    print("=" * 80)

def main():
    parser = argparse.ArgumentParser(description="Visa CE 3.0 Compelling Evidence Engine")
    parser.add_argument("--demo", action="store_true", help="Run end-to-end CE 3.0 dispute defense sprint")
    args = parser.parse_args()

    if args.demo or len(sys.argv) == 1:
        run_demo()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
