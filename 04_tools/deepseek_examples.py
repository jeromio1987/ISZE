"""
DeepSeek examples for ISZE work.
Run:  python 04_tools/deepseek_examples.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deepseek_utils import DeepSeekClient, MODEL_PRO, MODEL_FLASH


def ex_summarise(client):
    """Bulk summarisation - use FLASH, it is cheap and fast enough."""
    data = """
    ITUK Q3 FY2026:
    - Vehicle parts revenue: EUR 1.8M (+12% vs Q2)
    - Accessories: EUR 700K (+5% vs Q2)
    - Top movers: oil filters 15K units, clutch discs 8K, brake pads 6K
    - PMS capture rate 0.3% against a 3-5% expectation
    - EQ-HIT has no PN-to-service-interval mapping
    """
    print(client.chat(
        "Summarise this in 5 bullets, lead with the number that matters most:\n" + data,
        model=MODEL_FLASH,
    ))
    print("\n[" + client.usage_report() + "]")


def ex_pricing_analysis(client):
    """Analysis with a judgement call - use PRO, it reasons."""
    data = """
    D-Max EGR valve, PN 8983320160, sourced Thailand:
      ISZE list (PR00):   EUR 235.55
      Competitor A:       EUR 218.90
      Competitor B:       EUR 242.10
      IAM equivalent avg: EUR 220.00
    FX FY2026: 163.7 JPY/EUR. Source T discount factor 0.611.
    """
    print(client.chat(
        "Assess our price competitiveness on this part and state what you would "
        "do about it. Be specific and flag anything you are assuming.\n" + data,
        model=MODEL_PRO,
        max_tokens=3000,
    ))
    print("\n[" + client.usage_report() + "]")


def ex_batch(client):
    """Several items in one call - far cheaper than one call each."""
    rows = [
        "ITUK      | UIO 22,389 | rev EUR 2.5M | PMS capture 0.3%",
        "I-Motors  | UIO  8,000 | rev EUR 900K | PMS capture 1.2%",
        "UMI/UTI   | UIO  3,000 | rev EUR 400K | PMS capture 0.8%",
    ]
    print(client.chat(
        "For each distributor give: (1) the one insight that matters, "
        "(2) the single highest-value action, (3) the risk being ignored.\n\n"
        + "\n".join(rows),
        model=MODEL_PRO,
        max_tokens=3000,
    ))
    print("\n[" + client.usage_report() + "]")


EXAMPLES = {
    "1": ("Summarise a report (flash)", ex_summarise),
    "2": ("Pricing analysis (pro)", ex_pricing_analysis),
    "3": ("Batch distributor review (pro)", ex_batch),
}

if __name__ == "__main__":
    client = DeepSeekClient()

    choice = sys.argv[1] if len(sys.argv) > 1 else None
    if choice not in EXAMPLES:
        print("Usage: python 04_tools/deepseek_examples.py <number>\n")
        for k, (label, _) in EXAMPLES.items():
            print("  " + k + " - " + label)
        print("\nEach run costs roughly EUR 0.001 - 0.01.")
        sys.exit(0)

    label, fn = EXAMPLES[choice]
    print("=== " + label + " ===\n")
    fn(client)
