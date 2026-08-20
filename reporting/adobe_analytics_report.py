"""
adobe_analytics_report.py
--------------------------------------------------------------------------
Pulls a report from the Adobe Analytics 2.0 Reporting API and writes a
product-performance funnel (Product View -> Add to Cart -> Purchase) to CSV.

This portfolio project has no live Adobe Analytics instance, so the script
defaults to --mock, which loads sample_response.json (shaped exactly like a
real /reports response) instead of calling the API. Point it at real
credentials and drop --mock to run it against an actual report suite.

Usage:
    python3 adobe_analytics_report.py --mock
    python3 adobe_analytics_report.py --rsid northlinegoods-prod \
        --start-date 2026-07-01 --end-date 2026-07-31

Auth (real mode): Adobe Developer Console "Server-to-Server" OAuth credential.
Set these environment variables (or a .env file — see requirements.txt):
    ADOBE_CLIENT_ID
    ADOBE_CLIENT_SECRET
    ADOBE_ORG_ID
    ADOBE_GLOBAL_COMPANY_ID
--------------------------------------------------------------------------
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

try:
    import requests
except ImportError:  # requests is only needed in real (non-mock) mode
    requests = None

TOKEN_URL = "https://ims-na1.adobelogin.com/ims/token/v3"
REPORT_URL = "https://analytics.adobe.io/api/{company_id}/reports"

# Dimension/metric IDs used for this report — must exist in the report suite
# and correspond to the variables documented in tracking-plan.xlsx.
DIMENSION_ID = "variables/evar4"          # Product SKU
METRIC_IDS = [
    "metrics/event1",  # Product View
    "metrics/event2",  # Add to Cart
    "metrics/event9",  # Purchase
]
METRIC_LABELS = ["Product Views", "Adds to Cart", "Purchases"]

SKU_TO_NAME = {
    "NLG-JCK-1042": "Trail Runner Jacket",
    "NLG-JCK-1077": "Ridgeline Down Parka",
    "NLG-PCK-2011": "Summit 32L Pack",
    "NLG-BTS-3005": "Basecamp Waterproof Boot",
    "NLG-FLC-1090": "Alpine Fleece Half-Zip",
    "NLG-BTL-4002": "Insulated Field Bottle",
}


@dataclass
class AdobeAnalyticsClient:
    """Minimal client for the Adobe Analytics 2.0 Reporting API (real mode)."""

    client_id: str
    client_secret: str
    org_id: str
    global_company_id: str
    _access_token: str | None = None

    def _get_access_token(self) -> str:
        if self._access_token:
            return self._access_token
        if requests is None:
            raise RuntimeError("The 'requests' package is required for live API calls.")
        resp = requests.post(
            TOKEN_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "openid,AdobeID,read_organizations,additional_info.projectedProductContext",
            },
            timeout=15,
        )
        resp.raise_for_status()
        self._access_token = resp.json()["access_token"]
        return self._access_token

    def run_report(self, rsid: str, start_date: str, end_date: str) -> dict[str, Any]:
        """Requests a Product SKU x [Product View, Add to Cart, Purchase] report."""
        token = self._get_access_token()
        payload = {
            "rsid": rsid,
            "globalFilters": [
                {
                    "type": "dateRange",
                    "dateRange": f"{start_date}T00:00:00.000/{end_date}T23:59:59.999",
                }
            ],
            "metricContainer": {
                "metrics": [{"id": metric_id, "columnId": str(i)} for i, metric_id in enumerate(METRIC_IDS)]
            },
            "dimension": DIMENSION_ID,
            "settings": {"countRepeatInstances": True, "limit": 50, "page": 0},
        }
        resp = requests.post(
            REPORT_URL.format(company_id=self.global_company_id),
            headers={
                "Authorization": f"Bearer {token}",
                "x-api-key": self.client_id,
                "x-proxy-global-company-id": self.global_company_id,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()


def load_mock_response() -> dict[str, Any]:
    sample_path = Path(__file__).parent / "sample_response.json"
    with sample_path.open() as f:
        return json.load(f)


def response_to_dataframe(response: dict[str, Any]) -> pd.DataFrame:
    """Parses an Adobe Analytics 2.0 /reports response into a tidy DataFrame."""
    rows = response.get("rows", [])
    records = []
    for row in rows:
        sku = row["value"]
        views, adds, purchases = row["data"]
        records.append(
            {
                "Product SKU": sku,
                "Product Name": SKU_TO_NAME.get(sku, sku),
                METRIC_LABELS[0]: views,
                METRIC_LABELS[1]: adds,
                METRIC_LABELS[2]: purchases,
            }
        )
    df = pd.DataFrame(records)
    if df.empty:
        return df

    # Derived funnel-conversion metrics — computed client-side since the API
    # returns raw counters, not ratios.
    df["View -> Cart Rate"] = (df["Adds to Cart"] / df["Product Views"]).round(4)
    df["Cart -> Purchase Rate"] = (df["Purchases"] / df["Adds to Cart"]).round(4)
    df["View -> Purchase Rate"] = (df["Purchases"] / df["Product Views"]).round(4)
    return df.sort_values("Product Views", ascending=False).reset_index(drop=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Pull a product-funnel report from Adobe Analytics.")
    parser.add_argument("--mock", action="store_true", help="Use sample_response.json instead of a live API call.")
    parser.add_argument("--rsid", default="northlinegoods-prod", help="Report suite ID.")
    parser.add_argument(
        "--start-date",
        default=(date.today() - timedelta(days=30)).isoformat(),
        help="Report start date (YYYY-MM-DD). Defaults to 30 days ago.",
    )
    parser.add_argument("--end-date", default=date.today().isoformat(), help="Report end date (YYYY-MM-DD).")
    parser.add_argument("--out", default="product_funnel_report.csv", help="Output CSV path.")
    args = parser.parse_args()

    use_mock = args.mock or not all(
        os.environ.get(k) for k in ("ADOBE_CLIENT_ID", "ADOBE_CLIENT_SECRET", "ADOBE_ORG_ID", "ADOBE_GLOBAL_COMPANY_ID")
    )

    if use_mock:
        print("[mock mode] No live report suite is configured for this project — loading sample_response.json.")
        response = load_mock_response()
    else:
        client = AdobeAnalyticsClient(
            client_id=os.environ["ADOBE_CLIENT_ID"],
            client_secret=os.environ["ADOBE_CLIENT_SECRET"],
            org_id=os.environ["ADOBE_ORG_ID"],
            global_company_id=os.environ["ADOBE_GLOBAL_COMPANY_ID"],
        )
        print(f"Requesting report for rsid={args.rsid}, {args.start_date} to {args.end_date} ...")
        response = client.run_report(args.rsid, args.start_date, args.end_date)

    df = response_to_dataframe(response)
    if df.empty:
        print("No rows returned.")
        return 1

    out_path = Path(__file__).parent / args.out
    df.to_csv(out_path, index=False)

    print(f"\nProduct Funnel — {args.rsid} ({args.start_date} to {args.end_date})\n")
    print(df.to_string(index=False))
    print(f"\nSaved: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
