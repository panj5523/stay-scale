import re
from dataclasses import dataclass
from decimal import Decimal

from app.modules.recommendations.schemas import RecommendationRequest


@dataclass(frozen=True)
class FeedbackInterpretation:
    request: RecommendationRequest
    applied_changes: dict[str, object]
    warnings: list[str]


class RecommendationFeedbackInterpreter:
    def interpret(self, feedback: str, current: RecommendationRequest) -> FeedbackInterpretation:
        text = feedback.strip()
        values = current.model_dump()
        changes: dict[str, object] = {}
        warnings: list[str] = []

        if any(word in text for word in ("便宜", "省钱", "低价", "性价比")):
            values["travel_style"] = "value"
            changes["travel_style"] = "value"
        elif any(word in text for word in ("海景", "看海", "风景", "景观")):
            values["travel_style"] = "scenery"
            facilities = list(values["preferred_facilities"])
            if "sea_view" not in facilities:
                facilities.append("sea_view")
            values["preferred_facilities"] = facilities
            changes["travel_style"] = "scenery"
            changes["preferred_facilities"] = facilities
        elif any(word in text for word in ("舒适", "品质", "评分", "空调")):
            values["travel_style"] = "comfort"
            changes["travel_style"] = "comfort"
        elif any(word in text for word in ("家庭", "亲子", "孩子", "老人")):
            values["travel_style"] = "family"
            values["preferred_facilities"] = list(
                dict.fromkeys([*values["preferred_facilities"], "kitchen", "washer"])
            )
            changes["travel_style"] = "family"
            changes["preferred_facilities"] = values["preferred_facilities"]

        if any(word in text for word in ("大理镇", "双廊镇")):
            district = "双廊镇" if "双廊镇" in text else "大理镇"
            values["preferred_districts"] = [district]
            changes["preferred_districts"] = [district]

        budget_match = re.search(r"(?:预算|总价|控制在)\D{0,6}(\d{3,7})", text)
        if budget_match:
            budget = Decimal(budget_match.group(1))
            values["budget_total"] = budget
            changes["budget_total"] = str(budget)

        if "不要海景" in text or "不需要海景" in text:
            values["preferred_facilities"] = [
                item for item in values["preferred_facilities"] if item != "sea_view"
            ]
            changes["preferred_facilities"] = values["preferred_facilities"]

        if not changes:
            warnings.append("没有识别出可调整的偏好，已保留原推荐条件。")

        return FeedbackInterpretation(
            request=RecommendationRequest.model_validate(values),
            applied_changes=changes,
            warnings=warnings,
        )
