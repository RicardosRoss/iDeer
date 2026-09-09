"""Cross-day seen-repo memory for the GitHub source.

Keeps a JSON file mapping ``owner/repo`` to the date it was last shown and
its star count at that time, so daily runs can skip repos that were already
recommended within a recent window. One exception: a recently seen repo is
surfaced again when its stars grew substantially, carrying a
``star_growth_pct`` marker for downstream rendering.
"""

import os
from datetime import date, datetime

from core.cache_utils import atomic_write_json, safe_read_json

# Re-show a recently seen repo only if its stars grew by at least this ratio.
REGROWTH_RATIO = 1.5
# Drop entries older than this many days to bound the state file size.
PRUNE_AFTER_DAYS = 30


class SeenRepoStore:
    def __init__(self, path: str, window_days: int = 14):
        self.path = path
        self.window_days = window_days
        data = safe_read_json(path)
        self._data = data if isinstance(data, dict) else {}

    @staticmethod
    def _parse_date(value) -> date | None:
        try:
            return datetime.strptime(str(value), "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return None

    def _days_since(self, entry: dict, today: date) -> int | None:
        shown = self._parse_date(entry.get("date_shown"))
        if shown is None:
            return None
        return (today - shown).days

    def classify(self, repos: list[dict], today: date) -> tuple[list[dict], list[dict], int]:
        """Split repos into (new, regrowth, skipped_count).

        ``regrowth`` items are shallow copies of the input carrying an extra
        ``star_growth_pct`` key so prompts, templates, and reports can badge
        them. Repos seen within the window without significant star growth
        are dropped (counted in ``skipped_count``).
        """
        new, regrowth, skipped = [], [], 0
        for repo in repos:
            entry = self._data.get(repo.get("repo_name", ""))
            if entry is None:
                new.append(repo)
                continue
            days = self._days_since(entry, today)
            if days is None or days >= self.window_days:
                new.append(repo)
                continue
            prev_stars = entry.get("stars") or 0
            cur_stars = repo.get("stars") or 0
            if prev_stars > 0 and cur_stars >= prev_stars * REGROWTH_RATIO:
                marked = dict(repo)
                marked["star_growth_pct"] = round((cur_stars - prev_stars) * 100.0 / prev_stars)
                regrowth.append(marked)
            else:
                skipped += 1
        return new, regrowth, skipped

    def is_recent(self, repo_name: str, today: date) -> bool:
        entry = self._data.get(repo_name)
        if entry is None:
            return False
        days = self._days_since(entry, today)
        return days is not None and days < self.window_days

    def record(self, repos: list[dict], today: date) -> None:
        for repo in repos:
            name = repo.get("repo_name")
            if not name:
                continue
            self._data[name] = {
                "date_shown": today.strftime("%Y-%m-%d"),
                "stars": int(repo.get("stars") or 0),
            }
        self._prune(today)
        self.save()

    def _prune(self, today: date) -> None:
        stale = [
            name for name, entry in self._data.items()
            if self._days_since(entry, today) is None
            or self._days_since(entry, today) >= PRUNE_AFTER_DAYS
        ]
        for name in stale:
            del self._data[name]

    def save(self) -> None:
        try:
            atomic_write_json(self.path, self._data)
        except OSError as e:
            print(f"[github] Seen-repo state write failed: {e}")
