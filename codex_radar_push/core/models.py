from dataclasses import dataclass

from codex_radar_push.shared.hashing import stable_hash


@dataclass(frozen=True)
class RadarSection:
    key: str
    title: str
    updated_at: str
    summary: str
    change_basis: str | None = None

    @property
    def fingerprint(self) -> str:
        if self.change_basis is not None:
            return stable_hash(f"{self.key}\n{self.change_basis}")
        return stable_hash(f"{self.key}\n{self.updated_at}\n{self.summary}")


@dataclass(frozen=True)
class RadarSnapshot:
    sections: dict[str, RadarSection]
