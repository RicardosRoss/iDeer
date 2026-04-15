import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.config import CommonConfig, LLMConfig
from pipeline.report_generator import ReportGenerator


class QueueModel:
    def __init__(self, responses):
        self.responses = list(responses)
        self.prompts = []

    def inference(self, prompt, temperature=0.7):
        self.prompts.append(prompt)
        if not self.responses:
            raise AssertionError("No mock response left for QueueModel")
        return self.responses.pop(0)


def sample_recommendations():
    return {
        "github": [
            {
                "title": "agentscope-ai/ReMe",
                "repo_name": "agentscope-ai/ReMe",
                "summary": "A high-signal repository for agent memory control.",
                "description": "Memory editing and control for agents.",
                "url": "https://github.com/agentscope-ai/ReMe",
                "language": "Python",
                "highlights": ["agent memory", "control", "safety"],
                "score": 8.8,
                "stars": 1200,
                "stars_today": 140,
                "forks": 90,
            }
        ],
        "huggingface": [
            {
                "title": "A strong paper on agent robustness",
                "id": "paper-123",
                "summary": "Paper signal worth tracking.",
                "abstract": "Agent robustness under long-horizon workflows.",
                "url": "https://huggingface.co/papers/123",
                "_hf_type": "paper",
                "score": 8.1,
                "upvotes": 210,
            }
        ],
        "twitter": [
            {
                "title": "Thread on agent evals",
                "author_name": "Researcher",
                "author_username": "evals_lab",
                "summary": "A concise thread about agent evaluation priorities.",
                "text": "Agent evaluation needs better environment realism.",
                "url": "https://x.com/evals_lab/status/1",
                "created_at": "2026-04-13T10:00:00+00:00",
                "score": 7.9,
                "likes": 200,
                "retweets": 50,
                "replies": 12,
            }
        ],
    }


VALID_REPORT_JSON = """{
  "report_title": "Coding Agent Engineering Inflection Point",
  "subtitle": "Reliability and memory are becoming first-class product concerns.",
  "opening": "Today's signals point to a shift from agent demos to dependable engineering systems.",
  "themes": [
    {
      "title": "Reliability becomes the bottleneck",
      "narrative": "Both the repo and the paper emphasize hardening the operational layer around coding agents.",
      "signals": [
        {
          "source": "github",
          "title": "agentscope-ai/ReMe",
          "why_it_matters": "Shows momentum for memory-centric agent infrastructure.",
          "url": "https://github.com/agentscope-ai/ReMe"
        }
      ]
    }
  ],
  "interpretation": {
    "thesis": "The market is moving from model novelty toward infrastructure quality.",
    "implications": "Teams that solve reliability and memory will have the advantage."
  },
  "predictions": [
    {
      "prediction": "Tooling will expose more stateful debugging surfaces for agents.",
      "time_horizon": "1-3 months",
      "confidence": "medium",
      "rationale": "The strongest signals are around persistence and recovery."
    }
  ],
  "ideas": [
    {
      "title": "Agent failure replay dashboard",
      "detail": "Capture malformed generations and replay them for operator review.",
      "why_now": "Teams need better observability into failure modes."
    }
  ],
  "watchlist": [
    {
      "item": "Structured report generation support",
      "reason": "It can reduce brittle parsing in CI."
    }
  ]
}"""


class ReportGeneratorTest(unittest.TestCase):
    def setUp(self):
        self.llm_config = LLMConfig(
            provider="openai",
            model="dummy-model",
            base_url="https://example.com/v1",
            api_key="dummy-key",
            temperature=0.2,
        )
        self.common_config = CommonConfig(
            description="Agent / Safety / Trustworthy",
            num_workers=1,
            save=True,
            save_dir="./history",
        )
        self.generator = ReportGenerator(
            all_recs=sample_recommendations(),
            profile_text="Agent safety and evaluation researcher.",
            llm_config=self.llm_config,
            common_config=self.common_config,
            report_title="Daily Personal Briefing",
            min_score=4.0,
            max_items=6,
            theme_count=3,
            prediction_count=2,
            idea_count=2,
        )

    def test_generate_saves_raw_response_and_repairs_invalid_json(self):
        self.generator.model = QueueModel(
            [
                '{"report_title":"Bad JSON","opening":"This quote breaks " json"}',
                VALID_REPORT_JSON,
            ]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            self.generator.save_dir = tmpdir
            self.generator.email_cache_path = str(Path(tmpdir) / "report.html")

            report = self.generator.generate()

            self.assertEqual(report["report_title"], "Coding Agent Engineering Inflection Point")
            self.assertNotIn("generation_mode", report["metadata"])
            self.assertTrue((Path(tmpdir) / "report_raw_attempt1.txt").exists())
            self.assertFalse((Path(tmpdir) / "report_raw_attempt2.txt").exists())
            self.assertGreaterEqual(len(self.generator.model.prompts), 2)

    def test_generate_returns_fallback_report_and_saves_both_raw_attempts(self):
        self.generator.model = QueueModel(
            [
                '{"report_title":"Bad JSON","opening":"This quote breaks " json"}',
                '{"still":"broken"',
            ]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            self.generator.save_dir = tmpdir
            self.generator.email_cache_path = str(Path(tmpdir) / "report.html")

            report = self.generator.generate()

            self.assertIsNotNone(report)
            self.assertEqual(report["metadata"]["generation_mode"], "fallback")
            self.assertEqual(report["metadata"]["fallback_reason"], "llm_report_json_invalid")
            self.assertGreaterEqual(len(report["themes"]), 1)
            self.assertTrue((Path(tmpdir) / "report_raw_attempt1.txt").exists())
            self.assertTrue((Path(tmpdir) / "report_raw_attempt2.txt").exists())
            self.assertGreaterEqual(len(self.generator.model.prompts), 2)

    def test_render_email_and_save_work_for_fallback_report(self):
        fallback_report = self.generator._build_fallback_report(
            self.generator._filter_items(),
            reason="unit_test",
        )
        fallback_report["input_items"] = self.generator._filter_items()

        with tempfile.TemporaryDirectory() as tmpdir:
            self.generator.save_dir = tmpdir
            self.generator.email_cache_path = str(Path(tmpdir) / "report.html")

            self.generator.save(fallback_report)
            html = self.generator.render_email(fallback_report)

            self.assertTrue((Path(tmpdir) / "report.json").exists())
            self.assertTrue((Path(tmpdir) / "report.md").exists())
            self.assertTrue((Path(tmpdir) / "report.html").exists())
            self.assertIn("Daily Personal Briefing", html)


if __name__ == "__main__":
    unittest.main()
