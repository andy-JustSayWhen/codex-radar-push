import json
from pathlib import Path

from codex_radar_push.core.models import RadarSnapshot


def load_state(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path: Path, snapshot: RadarSnapshot, metadata: dict | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    state = {
        "sections": {
            key: {
                "fingerprint": section.fingerprint,
                "updated_at": section.updated_at,
                "summary": section.summary,
                "change_basis": section.change_basis,
            }
            for key, section in snapshot.sections.items()
        }
    }
    if metadata:
        state.update(metadata)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def changed_sections(state: dict, snapshot: RadarSnapshot) -> list[str]:
    prior_sections = state.get("sections") or {}
    if not prior_sections:
        return list(snapshot.sections)
    changed = []
    for key, section in snapshot.sections.items():
        prior = prior_sections.get(key) or {}
        if prior.get("fingerprint") == section.fingerprint:
            continue
        if key == "reset" and _is_reset_basis_migration(prior, section.summary, section.change_basis):
            continue
        else:
            changed.append(key)
    return changed


def _is_reset_basis_migration(prior: dict, current_summary: str, current_change_basis: str | None) -> bool:
    prior_summary = str(prior.get("summary") or "")
    prior_lines = _reset_status_lines(prior_summary)
    if not prior_lines:
        return False

    current_lines = _reset_status_lines(current_summary)
    if prior_lines != current_lines:
        return False

    prior_basis = str(prior.get("change_basis") or "")
    if not prior_basis or not current_change_basis:
        return True

    normalized_prior_basis = _normalize_reset_basis(prior_basis)
    return all(_normalize_reset_basis(line) in normalized_prior_basis for line in current_change_basis.splitlines() if line.strip())


def _reset_status_lines(summary: str) -> list[str]:
    prefixes = ("发重置卡", "硬重置")
    return [line.strip() for line in summary.splitlines() if line.strip().startswith(prefixes)]


def _normalize_reset_basis(value: str) -> str:
    return " ".join(value.replace("：", " ").replace(":", " ").split())
