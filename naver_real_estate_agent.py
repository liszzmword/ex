#!/usr/bin/env python3
"""Weekly Naver Real Estate agent.

- Targets:
  1) 안양시 만안구 현대아파트
  2) 안양시 동안구 부영아파트
- Fetches current listings and recent real transaction prices if available.
- Sends one summary email.
"""

from __future__ import annotations

import os
import smtplib
from dataclasses import dataclass
from datetime import datetime
from email.mime.text import MIMEText
from email.utils import formatdate
from typing import Any

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://new.land.naver.com"
DEFAULT_TIMEOUT = 20


@dataclass(frozen=True)
class TargetComplex:
    display_name: str
    query: str
    region_keyword: str


TARGETS = [
    TargetComplex(
        display_name="안양시 만안구 현대아파트",
        query="안양시 만안구 현대아파트",
        region_keyword="만안구",
    ),
    TargetComplex(
        display_name="안양시 동안구 부영아파트",
        query="안양시 동안구 부영아파트",
        region_keyword="동안구",
    ),
]


class NaverLandClient:
    def __init__(self) -> None:
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Referer": f"{BASE_URL}/",
            "Accept": "application/json, text/plain, */*",
        }

    def _get_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        query = f"?{urlencode(params)}" if params else ""
        req = Request(f"{BASE_URL}{path}{query}", headers=self.headers)
        with urlopen(req, timeout=DEFAULT_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def search_complex(self, keyword: str) -> list[dict[str, Any]]:
        payload = self._get_json("/api/search", {"keyword": keyword})
        complexes = payload.get("complexes", [])
        return [c for c in complexes if str(c.get("complexNo", "")).isdigit()]

    def pick_best_complex(self, target: TargetComplex) -> dict[str, Any]:
        candidates = self.search_complex(target.query)
        if not candidates:
            raise RuntimeError(f"검색 결과가 없습니다: {target.query}")

        def score(item: dict[str, Any]) -> int:
            text = " ".join(
                [
                    str(item.get("complexName", "")),
                    str(item.get("cortarAddress", "")),
                    str(item.get("realEstateTypeName", "")),
                ]
            )
            s = 0
            if target.region_keyword in text:
                s += 4
            if "아파트" in text:
                s += 2
            if any(k in text for k in ["현대", "부영"]):
                s += 1
            return s

        return sorted(candidates, key=score, reverse=True)[0]

    def get_listings(self, complex_no: int | str) -> list[dict[str, Any]]:
        params = {
            "realEstateType": "APT:PRE",
            "tradeType": "A1:B1:B2",
            "tag": ":::",
            "rentPriceMin": 0,
            "rentPriceMax": 900000000,
            "priceMin": 0,
            "priceMax": 900000000,
            "areaMin": 0,
            "areaMax": 900000000,
            "oldBuildYears": "",
            "recentlyBuildYears": "",
            "minHouseHoldCount": "",
            "maxHouseHoldCount": "",
            "showArticle": "false",
            "sameAddr": "false",
            "minMaintenanceCost": "",
            "maxMaintenanceCost": "",
            "priceType": "RETAIL",
        }
        payload = self._get_json(f"/api/articles/complex/{complex_no}", params)
        return payload.get("articleList", [])

    def get_real_transactions(self, complex_no: int | str, area_no: int | str | None) -> list[dict[str, Any]]:
        if not area_no:
            return []

        params = {"tradeType": "A1", "areaNo": area_no, "year": "5"}
        payload = self._get_json(f"/api/complexes/{complex_no}/prices/real", params)

        prices = payload.get("realPriceOnMonthList") or payload.get("realPriceList") or []

        normalized: list[dict[str, Any]] = []
        for row in prices:
            if "dealYear" in row:
                month = f"{row.get('dealYear')}-{int(row.get('dealMonth', 0)):02d}"
            else:
                month = str(row.get("month", ""))
            normalized.append(
                {
                    "month": month,
                    "min": row.get("minDealPrice") or row.get("minPrice") or row.get("dealPrice"),
                    "max": row.get("maxDealPrice") or row.get("maxPrice") or row.get("dealPrice"),
                    "count": row.get("dealCount") or row.get("count") or "-",
                }
            )
        return normalized[:6]


def format_listing_line(article: dict[str, Any]) -> str:
    trade = article.get("tradeTypeName", "-")
    price = article.get("dealOrWarrantPrc", "-")
    spec1 = article.get("areaName", "")
    spec2 = article.get("floorInfo", "")
    direction = article.get("direction", "")
    desc = article.get("articleFeatureDesc", "")
    broker = article.get("realtorName", "")
    return f"- [{trade}] {price} / {spec1} {spec2} {direction} | {desc} | 중개사:{broker}".strip()


def build_report(data: list[dict[str, Any]]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines: list[str] = [f"네이버부동산 주간 리포트 ({now})", ""]

    for section in data:
        lines.append(f"## {section['target_name']}")
        lines.append(f"- 단지명: {section['complex_name']} (complexNo={section['complex_no']})")
        lines.append(f"- 주소: {section['address']}")

        listings = section["listings"]
        lines.append(f"- 현재 매물 수집 건수: {len(listings)}")
        if listings:
            lines.append("- 상위 매물:")
            for art in listings[:10]:
                lines.append(format_listing_line(art))
        else:
            lines.append("- 수집된 매물이 없습니다.")

        trades = section["real_transactions"]
        lines.append("- 최근 실거래:")
        if trades:
            for t in trades:
                lines.append(f"  - {t['month']}: {t['min']}~{t['max']} (거래건수 {t['count']})")
        else:
            lines.append("  - 실거래 데이터를 찾지 못했습니다.")
        lines.append("")

    return "\n".join(lines)


def send_email(subject: str, body: str) -> None:
    smtp_host = os.environ["SMTP_HOST"]
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.environ["SMTP_USER"]
    smtp_password = os.environ["SMTP_PASSWORD"]
    mail_from = os.getenv("MAIL_FROM", smtp_user)
    mail_to = os.getenv("MAIL_TO", "liszzm@skku.edu")

    msg = MIMEText(body, _subtype="plain", _charset="utf-8")
    msg["Subject"] = subject
    msg["From"] = mail_from
    msg["To"] = mail_to
    msg["Date"] = formatdate(localtime=True)

    with smtplib.SMTP(smtp_host, smtp_port) as smtp:
        smtp.starttls()
        smtp.login(smtp_user, smtp_password)
        smtp.sendmail(mail_from, [mail_to], msg.as_string())


def run() -> None:
    client = NaverLandClient()
    collected: list[dict[str, Any]] = []

    for target in TARGETS:
        complex_info = client.pick_best_complex(target)
        complex_no = complex_info["complexNo"]
        listings = client.get_listings(complex_no)
        area_no = listings[0].get("areaNo") if listings else None
        real_tx = client.get_real_transactions(complex_no, area_no)

        collected.append(
            {
                "target_name": target.display_name,
                "complex_name": complex_info.get("complexName", "-"),
                "complex_no": complex_no,
                "address": complex_info.get("cortarAddress", "-"),
                "listings": listings,
                "real_transactions": real_tx,
            }
        )

    body = build_report(collected)
    subject = f"[주간 부동산] 안양 현대/부영 매물 요약 - {datetime.now():%Y-%m-%d}"
    send_email(subject, body)


if __name__ == "__main__":
    run()
