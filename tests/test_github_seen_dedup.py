import sys
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.cache_utils import atomic_write_json
from core.seen_store import REGROWTH_RATIO, SeenRepoStore
from fetchers.github_fetcher import search_rising_repos


def repo(name, stars=100, **extra):
    owner, _, short = name.partition("/")
    item = {
        "repo_name": name,
        "owner": owner,
        "name": short,
        "description": f"desc of {name}",
        "language": "Python",
        "stars": stars,
        "stars_today": 10,
        "forks": 5,
        "repo_url": f"https://github.com/{name}",
        "built_by": [],
    }
    item.update(extra)
    return item


class SeenRepoStoreTest(unittest.TestCase):
    def setUp(self):
        import tempfile

        self.tmp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.tmp.name) / "github_seen_repos.json")

    def tearDown(self):
        self.tmp.cleanup()

    def test_fresh_store_classifies_everything_new(self):
        store = SeenRepoStore(self.path)
        today = date(2026, 9, 9)
        new, regrowth, skipped = store.classify([repo("a/a"), repo("b/b")], today)
        self.assertEqual([r["repo_name"] for r in new], ["a/a", "b/b"])
        self.assertEqual(regrowth, [])
        self.assertEqual(skipped, 0)

    def test_recorded_repo_is_skipped_next_day(self):
        store = SeenRepoStore(self.path)
        day1 = date(2026, 9, 1)
        store.record([repo("a/a", stars=1000)], day1)

        store = SeenRepoStore(self.path)
        new, regrowth, skipped = store.classify([repo("a/a", stars=1010)], date(2026, 9, 2))
        self.assertEqual(new, [])
        self.assertEqual(regrowth, [])
        self.assertEqual(skipped, 1)

    def test_significant_growth_reshows_with_pct(self):
        store = SeenRepoStore(self.path)
        store.record([repo("a/a", stars=1000)], date(2026, 9, 1))

        store = SeenRepoStore(self.path)
        new, regrowth, skipped = store.classify(
            [repo("a/a", stars=1600)], date(2026, 9, 2)
        )
        self.assertEqual(new, [])
        self.assertEqual(skipped, 0)
        self.assertEqual(len(regrowth), 1)
        self.assertEqual(regrowth[0]["star_growth_pct"], 60)

    def test_below_threshold_growth_is_still_skipped(self):
        store = SeenRepoStore(self.path)
        store.record([repo("a/a", stars=1000)], date(2026, 9, 1))

        store = SeenRepoStore(self.path)
        # 1.49x stays suppressed; only >= REGROWTH_RATIO re-shows
        new, regrowth, skipped = store.classify(
            [repo("a/a", stars=int(1000 * (REGROWTH_RATIO - 0.01)))], date(2026, 9, 2)
        )
        self.assertEqual((new, regrowth, skipped), ([], [], 1))

    def test_window_expiry_makes_repo_new_again(self):
        store = SeenRepoStore(self.path)
        store.record([repo("a/a", stars=1000)], date(2026, 9, 1))

        store = SeenRepoStore(self.path, window_days=14)
        new, _, _ = store.classify([repo("a/a", stars=1000)], date(2026, 9, 15))
        self.assertEqual([r["repo_name"] for r in new], ["a/a"])

    def test_record_prunes_stale_entries(self):
        store = SeenRepoStore(self.path)
        old = date(2026, 8, 1)
        store.record([repo("old/old", stars=10)], old)

        store = SeenRepoStore(self.path)
        store.record([repo("new/new", stars=20)], date(2026, 9, 9))
        data = store._data
        self.assertIn("new/new", data)
        self.assertNotIn("old/old", data)

    def test_corrupt_state_file_is_ignored(self):
        Path(self.path).write_text("{not json", encoding="utf-8")
        store = SeenRepoStore(self.path)
        new, _, _ = store.classify([repo("a/a")], date(2026, 9, 9))
        self.assertEqual(len(new), 1)

    def test_is_recent(self):
        store = SeenRepoStore(self.path)
        store.record([repo("a/a", stars=1)], date(2026, 9, 8))
        self.assertTrue(store.is_recent("a/a", date(2026, 9, 9)))
        self.assertFalse(store.is_recent("b/b", date(2026, 9, 9)))


class SearchRisingReposTest(unittest.TestCase):
    def _mock_response(self, items):
        resp = MagicMock()
        resp.raise_for_status.return_value = None
        resp.json.return_value = {"items": items}
        return resp

    @patch("fetchers.github_fetcher.requests.get")
    def test_maps_search_fields_to_repo_shape(self, mock_get):
        mock_get.return_value = self._mock_response([
            {
                "full_name": "owner/repo",
                "name": "repo",
                "owner": {"login": "owner"},
                "description": "A rising repo",
                "language": "Rust",
                "stargazers_count": 1234,
                "forks_count": 42,
                "html_url": "https://github.com/owner/repo",
            }
        ])
        repos = search_rising_repos()
        self.assertEqual(len(repos), 1)
        item = repos[0]
        self.assertEqual(item["repo_name"], "owner/repo")
        self.assertEqual(item["stars"], 1234)
        self.assertEqual(item["forks"], 42)
        self.assertEqual(item["repo_url"], "https://github.com/owner/repo")
        self.assertTrue(item["is_supplement"])
        self.assertEqual(item["stars_today"], 0)
        # query must target recently created repos with a star floor
        query = mock_get.call_args[1]["params"]["q"]
        self.assertIn("created:>=", query)
        self.assertIn("stars:>", query)

    @patch("fetchers.github_fetcher.requests.get")
    def test_network_error_returns_empty(self, mock_get):
        mock_get.side_effect = RuntimeError("boom")
        self.assertEqual(search_rising_repos(), [])


if __name__ == "__main__":
    unittest.main()
