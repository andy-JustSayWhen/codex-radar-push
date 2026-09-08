"""Normalize the site's live benchmark records without a model allowlist."""
from dataclasses import asdict, dataclass
from datetime import datetime
import json
import math


@dataclass(frozen=True)
class Measurement:
    score: float
    tasks: float
    minutes: float | None
    updated_at: str


@dataclass(frozen=True)
class ModelScore:
    model: str
    effort: str
    software: Measurement | None
    visual: Measurement | None

    @property
    def name(self) -> str:
        return f"{self.model} {self.effort}".strip()

    @property
    def composite(self) -> float | None:
        return self._weighted("score")

    @property
    def minutes(self) -> float | None:
        return self._weighted("minutes")

    def _weighted(self, field: str) -> float | None:
        if self.software is None or self.visual is None:
            return None
        left, right = getattr(self.software, field), getattr(self.visual, field)
        if left is None or right is None:
            return None
        return (left * self.software.tasks + right * self.visual.tasks) / (self.software.tasks + self.visual.tasks)


@dataclass(frozen=True)
class IntelligenceReport:
    rows: tuple[ModelScore, ...]
    software_updated_at: str
    visual_updated_at: str

    @property
    def change_basis(self) -> str:
        rows = [asdict(row) for row in self.rows]
        for row in rows:
            for kind in ("software", "visual"):
                if row[kind] is not None:
                    row[kind].pop("updated_at")
        return json.dumps(rows, ensure_ascii=False, sort_keys=True, allow_nan=False)


def build_report(software: dict, visual: dict) -> IntelligenceReport:
    schema = (software.get("schema"), software.get("mode")) if isinstance(software, dict) else None
    if schema not in {(3, "equal_latest_3"), (2, "weighted_latest_3")}:
        raise ValueError("软件工程数据格式已变化，请检查网站接口")
    task_field = "total" if schema[0] == 3 else "weighted_total"
    left = _measurements(software, task_field, "软件工程")
    right = _measurements(visual, "valid_tasks", "视觉空间")
    rows = tuple(ModelScore(model, effort, left.get((model, effort)), right.get((model, effort)))
                 for model, effort in sorted(left.keys() | right.keys()))
    return IntelligenceReport(rows, _updated_at(software), _updated_at(visual))


def _updated_at(payload: dict) -> str:
    value = payload.get("source_updated_at")
    if not isinstance(value, str) or not value.strip():
        raise ValueError("智商数据缺少源更新时间")
    _timestamp(value)
    return value


def _measurements(payload: dict, task_field: str, label: str) -> dict:
    if not isinstance(payload, dict) or not isinstance(payload.get("points"), list):
        raise ValueError(f"{label}数据格式无效")
    updated_at = _updated_at(payload)
    result = {}
    for point in payload["points"]:
        if not isinstance(point, dict):
            raise ValueError(f"{label}成绩记录格式无效")
        model, effort = point.get("model"), point.get("effort")
        if not isinstance(model, str) or not model.strip() or not isinstance(effort, str):
            raise ValueError(f"{label}成绩缺少模型或档位")
        if any(char in model + effort for char in "\r\n\t`"):
            raise ValueError(f"{label}模型或档位含无效字符")
        score = _number(point.get("iq"))
        tasks = _number(point.get(task_field))
        if score is None or tasks is None or tasks <= 0:
            continue
        row = Measurement(score, tasks, _number(point.get("average_minutes")),
                          point.get("source_updated_at") or point.get("latest_graded_at") or updated_at)
        key = (model.strip(), effort.strip())
        timestamp = _timestamp(row.updated_at)
        previous = result.get(key)
        if previous is None or timestamp > _timestamp(previous.updated_at):
            result[key] = row
        elif timestamp == _timestamp(previous.updated_at) and row != previous:
            raise ValueError(f"{label}存在同时间的冲突成绩")
    if not result:
        raise ValueError(f"{label}没有可用的模型数据")
    return result


def _number(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError("智商数据包含无效数值")
    try:
        number = float(value)
    except (ValueError, TypeError):
        raise ValueError("智商数据包含无效数值") from None
    if not math.isfinite(number) or number < 0:
        raise ValueError("智商数据包含无效数值")
    return number


def _timestamp(value: str) -> float:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError
        return parsed.timestamp()
    except (AttributeError, TypeError, ValueError):
        raise ValueError("智商数据源更新时间无效") from None
