import unittest

from naver_real_estate_agent import build_report, format_listing_line


class ReportFormatTest(unittest.TestCase):
    def test_format_listing_line_contains_core_fields(self):
        line = format_listing_line(
            {
                "tradeTypeName": "매매",
                "dealOrWarrantPrc": "8억",
                "areaName": "84A",
                "floorInfo": "10/20",
                "direction": "남향",
                "articleFeatureDesc": "채광좋음",
                "realtorName": "좋은공인중개사",
            }
        )
        self.assertIn("매매", line)
        self.assertIn("8억", line)
        self.assertIn("좋은공인중개사", line)

    def test_build_report_includes_transactions(self):
        text = build_report(
            [
                {
                    "target_name": "안양시 만안구 현대아파트",
                    "complex_name": "현대",
                    "complex_no": 123,
                    "address": "안양시 만안구",
                    "listings": [],
                    "real_transactions": [
                        {"month": "2026-01", "min": "7억", "max": "8억", "count": 2}
                    ],
                }
            ]
        )
        self.assertIn("최근 실거래", text)
        self.assertIn("2026-01", text)


if __name__ == "__main__":
    unittest.main()
