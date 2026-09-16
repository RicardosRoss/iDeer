import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


SAMPLE_LISTING = """<html><body>
<dl id="articles">
<dt><a title="Abstract" href="/abs/2609.11111">2609.11111</a> <a title="Download PDF" href="/pdf/2609.11111">[pdf]</a></dt>
<dd><div class="list-title">Title: Demo Paper One</div><p class="mathjax">First demo abstract.</p></dd>
<dt><a title="Abstract" href="/abs/2609.22222">2609.22222</a> <a title="Download PDF" href="/pdf/2609.22222">[pdf]</a></dt>
<dd><div class="list-title">Title: Demo Paper Two</div><p class="mathjax">Second demo abstract.</p></dd>
</dl>
</body></html>
"""


class FakeResponse:
    def __init__(self, text: str = "", status_code: int = 200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Error", response=self)


class GetArxivNewPapersTest(unittest.TestCase):
    def test_parses_listing_page_into_papers(self):
        from fetchers.arxiv_fetcher import get_arxiv_new_papers

        with patch("fetchers.arxiv_fetcher.requests.get", return_value=FakeResponse(SAMPLE_LISTING)):
            papers = get_arxiv_new_papers("cs.MA")

        self.assertEqual(len(papers), 2)
        first = papers[0]
        self.assertEqual(first["title"], "Demo Paper One")
        self.assertEqual(first["arxiv_id"], "2609.11111")
        self.assertEqual(first["abstract"], "First demo abstract.")
        self.assertEqual(first["pdf_url"], "https://arxiv.org/pdf/2609.11111")
        self.assertEqual(first["abstract_url"], "https://arxiv.org/abs/2609.11111")
        self.assertEqual(papers[1]["title"], "Demo Paper Two")

    def test_respects_max_results(self):
        from fetchers.arxiv_fetcher import get_arxiv_new_papers

        with patch("fetchers.arxiv_fetcher.requests.get", return_value=FakeResponse(SAMPLE_LISTING)):
            papers = get_arxiv_new_papers("cs.MA", max_results=1)

        self.assertEqual(len(papers), 1)

    def test_transient_timeout_is_retried_until_success(self):
        from fetchers.arxiv_fetcher import get_arxiv_new_papers

        side_effect = [
            requests.Timeout("Read timed out."),
            requests.Timeout("Read timed out."),
            FakeResponse(SAMPLE_LISTING),
        ]
        with patch("fetchers.arxiv_fetcher.requests.get", side_effect=side_effect) as mock_get, \
                patch("time.sleep") as mock_sleep:
            papers = get_arxiv_new_papers("cs.MA")

        self.assertEqual(len(papers), 2)
        self.assertEqual(mock_get.call_count, 3)
        self.assertEqual(
            [call.args[0] for call in mock_sleep.call_args_list], [15, 30]
        )

    def test_retryable_http_status_is_retried(self):
        from fetchers.arxiv_fetcher import get_arxiv_new_papers

        side_effect = [
            FakeResponse(status_code=503),
            FakeResponse(SAMPLE_LISTING),
        ]
        with patch("fetchers.arxiv_fetcher.requests.get", side_effect=side_effect) as mock_get, \
                patch("time.sleep"):
            papers = get_arxiv_new_papers("cs.MA")

        self.assertEqual(len(papers), 2)
        self.assertEqual(mock_get.call_count, 2)

    def test_permanent_http_error_is_not_retried(self):
        from fetchers.arxiv_fetcher import get_arxiv_new_papers

        with patch("fetchers.arxiv_fetcher.requests.get", return_value=FakeResponse(status_code=404)) as mock_get:
            with self.assertRaises(requests.HTTPError):
                get_arxiv_new_papers("cs.NOPE")

        self.assertEqual(mock_get.call_count, 1)

    def test_all_attempts_exhausted_raises(self):
        from fetchers.arxiv_fetcher import get_arxiv_new_papers

        with patch("fetchers.arxiv_fetcher.requests.get", side_effect=requests.Timeout("Read timed out.")) as mock_get, \
                patch("time.sleep"):
            with self.assertRaises(requests.RequestException):
                get_arxiv_new_papers("cs.MA")

        self.assertEqual(mock_get.call_count, 3)


class FetchPapersForCategoriesTest(unittest.TestCase):
    def test_failed_category_does_not_discard_successful_ones(self):
        from fetchers.arxiv_fetcher import fetch_papers_for_categories

        def fake_fetch(category, max_results):
            if category == "cs.SE":
                raise requests.RequestException("all attempts failed")
            return [{"title": f"paper in {category}", "arxiv_id": "2609.1"}]

        with patch("fetchers.arxiv_fetcher.get_arxiv_new_papers", side_effect=fake_fetch), \
                patch("time.sleep"):
            result = fetch_papers_for_categories(["cs.SE", "cs.MA"])

        self.assertEqual(list(result.keys()), ["cs.MA"])
        self.assertEqual(result["cs.MA"][0]["title"], "paper in cs.MA")

    def test_all_categories_failed_raises(self):
        from fetchers.arxiv_fetcher import fetch_papers_for_categories

        with patch(
            "fetchers.arxiv_fetcher.get_arxiv_new_papers",
            side_effect=requests.Timeout("Read timed out."),
        ), patch("time.sleep"):
            with self.assertRaises(RuntimeError):
                fetch_papers_for_categories(["cs.SE", "cs.MA"])


if __name__ == "__main__":
    unittest.main()
