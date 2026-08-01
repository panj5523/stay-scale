import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.modules.preference_parsing.schemas import ExtractionEvidence, ParsedPreferences

PARSER_NAME = "local-rule-parser"
PARSER_VERSION = "zh-rules-v1"

CHINESE_NUMBERS = {
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
}

FACILITY_KEYWORDS = {
    "wifi": ("无线网", "无线网络", "wifi", "WiFi"),
    "air_conditioning": ("空调",),
    "kitchen": ("厨房", "做饭", "可做饭"),
    "washer": ("洗衣机", "洗衣"),
    "parking": ("停车", "停车位"),
    "sea_view": ("海景", "看海", "洱海景"),
    "ground_floor": ("一楼", "低楼层", "老人方便"),
}

DISTRICTS = ("大理镇", "双廊镇")


@dataclass(slots=True)
class ParseResult:
    draft: ParsedPreferences
    evidence: list[ExtractionEvidence]
    missing_fields: list[str]
    warnings: list[str]
    confidence: Decimal


class ChinesePreferenceParser:
    def parse(self, text: str, reference_date: date | None = None) -> ParseResult:
        normalized = " ".join(text.strip().split())
        reference = reference_date or date.today()
        values: dict[str, object] = {
            "preferred_facilities": [],
            "preferred_districts": [],
            "risk_aversion": "medium",
        }
        evidence: list[ExtractionEvidence] = []
        warnings: list[str] = []

        self._parse_city(normalized, values, evidence)
        self._parse_dates(normalized, reference, values, evidence, warnings)
        self._parse_guests(normalized, values, evidence)
        self._parse_budget(normalized, values, evidence)
        self._parse_facilities(normalized, values, evidence)
        self._parse_districts(normalized, values, evidence)
        self._parse_style(normalized, values, evidence)
        self._parse_risk(normalized, values, evidence)

        try:
            draft = ParsedPreferences.model_validate(values)
        except ValueError:
            values.pop("check_in", None)
            values.pop("check_out", None)
            warnings.append("识别到的离店日期没有晚于入住日期，请手动确认日期。")
            evidence = [item for item in evidence if item.field not in {"check_in", "check_out"}]
            draft = ParsedPreferences.model_validate(values)

        required = ("city", "check_in", "check_out", "guests")
        missing_fields = [field for field in required if getattr(draft, field) is None]
        recognized_core = len(required) - len(missing_fields)
        optional_bonus = min(2, len(evidence) - recognized_core)
        confidence = Decimal(str(min(0.98, 0.2 + recognized_core * 0.17 + optional_bonus * 0.05)))
        if missing_fields:
            warnings.append("仍有必要信息未识别，请在确认前补充。")

        return ParseResult(
            draft=draft,
            evidence=evidence,
            missing_fields=missing_fields,
            warnings=warnings,
            confidence=confidence.quantize(Decimal("0.001")),
        )

    @staticmethod
    def _add_evidence(
        evidence: list[ExtractionEvidence], field: str, matched: str, value: object
    ) -> None:
        evidence.append(
            ExtractionEvidence(field=field, matched_text=matched, normalized_value=str(value))
        )

    def _parse_city(
        self, text: str, values: dict[str, object], evidence: list[ExtractionEvidence]
    ) -> None:
        aliases = {"大理": "大理市", "丽江": "丽江市", "昆明": "昆明市"}
        for keyword, city in aliases.items():
            if keyword in text:
                values["city"] = city
                self._add_evidence(evidence, "city", keyword, city)
                return
        match = re.search(r"([\u4e00-\u9fff]{2,8}市)", text)
        if match:
            values["city"] = match.group(1)
            self._add_evidence(evidence, "city", match.group(0), match.group(1))

    def _parse_dates(
        self,
        text: str,
        reference: date,
        values: dict[str, object],
        evidence: list[ExtractionEvidence],
        warnings: list[str],
    ) -> None:
        iso = re.search(
            r"(20\d{2}-\d{1,2}-\d{1,2})\s*(?:到|至|—|~)\s*(20\d{2}-\d{1,2}-\d{1,2})", text
        )
        if iso:
            try:
                check_in = date.fromisoformat(iso.group(1))
                check_out = date.fromisoformat(iso.group(2))
            except ValueError:
                warnings.append("日期格式无法识别，请手动选择入住和离店日期。")
                return
            values.update(check_in=check_in, check_out=check_out)
            self._add_evidence(evidence, "check_in", iso.group(1), check_in)
            self._add_evidence(evidence, "check_out", iso.group(2), check_out)
            return

        pattern = re.compile(
            r"(?:(?P<year>20\d{2})年)?(?P<in_month>\d{1,2})月(?P<in_day>\d{1,2})日?"
            r"\s*(?:到|至|—|-|~)\s*(?:(?P<out_month>\d{1,2})月)?(?P<out_day>\d{1,2})日?"
        )
        match = pattern.search(text)
        if not match:
            return
        year = int(match.group("year") or reference.year)
        out_month = int(match.group("out_month") or match.group("in_month"))
        try:
            check_in = date(year, int(match.group("in_month")), int(match.group("in_day")))
            check_out = date(year, out_month, int(match.group("out_day")))
        except ValueError:
            warnings.append("日期超出有效范围，请手动选择入住和离店日期。")
            return
        values.update(check_in=check_in, check_out=check_out)
        self._add_evidence(evidence, "check_in", match.group(0), check_in)
        self._add_evidence(evidence, "check_out", match.group(0), check_out)

    def _parse_guests(
        self, text: str, values: dict[str, object], evidence: list[ExtractionEvidence]
    ) -> None:
        match = re.search(r"(\d{1,2}|[一二两三四五六七八九十])\s*(?:个?人|位)", text)
        if not match:
            return
        raw = match.group(1)
        guests = int(raw) if raw.isdigit() else CHINESE_NUMBERS[raw]
        if 1 <= guests <= 20:
            values["guests"] = guests
            self._add_evidence(evidence, "guests", match.group(0), guests)

    def _parse_budget(
        self, text: str, values: dict[str, object], evidence: list[ExtractionEvidence]
    ) -> None:
        patterns = (
            r"(?:预算|总价|控制在)\D{0,6}(\d{3,7}(?:\.\d+)?)",
            r"(\d{3,7}(?:\.\d+)?)\s*(?:元)?\s*(?:以内|以下|封顶)",
        )
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                budget = Decimal(match.group(1))
                values["budget_total"] = budget
                self._add_evidence(evidence, "budget_total", match.group(0), budget)
                return

    def _parse_facilities(
        self, text: str, values: dict[str, object], evidence: list[ExtractionEvidence]
    ) -> None:
        facilities: list[str] = values["preferred_facilities"]  # type: ignore[assignment]
        for code, keywords in FACILITY_KEYWORDS.items():
            matched = next((keyword for keyword in keywords if keyword in text), None)
            if matched:
                facilities.append(code)
                self._add_evidence(evidence, "preferred_facilities", matched, code)

    def _parse_districts(
        self, text: str, values: dict[str, object], evidence: list[ExtractionEvidence]
    ) -> None:
        districts: list[str] = values["preferred_districts"]  # type: ignore[assignment]
        for district in DISTRICTS:
            if district in text:
                districts.append(district)
                self._add_evidence(evidence, "preferred_districts", district, district)

    def _parse_style(
        self, text: str, values: dict[str, object], evidence: list[ExtractionEvidence]
    ) -> None:
        style_keywords = (
            ("family", ("亲子", "家庭", "带孩子", "带老人")),
            ("scenery", ("海景", "风景", "景观", "看海")),
            ("comfort", ("舒适", "品质", "住得好", "安静")),
            ("value", ("省钱", "便宜", "性价比", "实惠")),
        )
        for style, keywords in style_keywords:
            matched = next((keyword for keyword in keywords if keyword in text), None)
            if matched:
                values["travel_style"] = style
                self._add_evidence(evidence, "travel_style", matched, style)
                return

    def _parse_risk(
        self, text: str, values: dict[str, object], evidence: list[ExtractionEvidence]
    ) -> None:
        high_keywords = ("免费取消", "可取消", "行程可能变", "稳妥")
        low_keywords = ("不可退", "特价优先", "确定出行")
        for risk, keywords in (("high", high_keywords), ("low", low_keywords)):
            matched = next((keyword for keyword in keywords if keyword in text), None)
            if matched:
                values["risk_aversion"] = risk
                self._add_evidence(evidence, "risk_aversion", matched, risk)
                return
