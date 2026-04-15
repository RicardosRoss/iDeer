import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.config import CommonConfig, LLMConfig
from pipeline.report_generator import ReportGenerator


class SequenceModel:
    def __init__(self, responses):
        self.responses = list(responses)
        self.prompts = []

    def inference(self, prompt, temperature=0.7):
        self.prompts.append(prompt)
        if not self.responses:
            raise AssertionError("No more model responses configured.")
        return self.responses.pop(0)


def build_sample_recommendations():
    return {
        "github": [
            {
                "title": "Hermes Agent",
                "summary": "Agent framework with memory and workflow orchestration.",
                "url": "https://example.com/hermes",
                "score": 8.6,
                "repo_name": "NousResearch/hermes-agent",
                "language": "Python",
                "description": "A repository for resilient autonomous agents.",
                "highlights": ["memory", "orchestration"],
                "stars": 1200,
                "stars_today": 84,
                "forks": 110,
            }
        ],
        "arxiv": [
            {
                "title": "Resilient Write for Coding Agents",
                "summary": "A paper on write reliability for long-running coding agents.",
                "url": "https://example.com/resilient-write",
                "score": 8.1,
                "category": "cs.SE",
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
          "title": "Hermes Agent",
          "why_it_matters": "Shows momentum for memory-centric agent infrastructure.",
          "url": "https://example.com/hermes"
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


INVALID_REPORT_JSON = """{
  "report_title": "Bad JSON",
  "subtitle": "Invalid output",
  "opening": "This line breaks from "prototype" to "production"."
}"""


class ReportGeneratorTest(unittest.TestCase):
    def setUp(self):
        self.all_recs = build_sample_recommendations()
        self.llm_config = LLMConfig(
            provider="openai",
            model="dummy-model",
            base_url="https://example.com/v1",
            api_key="dummy-key",
            temperature=0.2,
        )
        self.profile_text = "I care about coding agents, infrastructure reliability, and memory systems."

    def make_generator(self, save_dir):
        common_config = CommonConfig(
            description="Agent infra",
            num_workers=1,
            save=True,
            save_dir=save_dir,
        )
        return ReportGenerator(
            all_recs=self.all_recs,
            profile_text=self.profile_text,
            llm_config=self.llm_config,
            common_config=common_config,
            report_title="Daily Personal Briefing",
            min_score=4.0,
            max_items=6,
            theme_count=3,
            prediction_count=2,
            idea_count=2,
        )

    def test_generate_retries_once_after_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = self.make_generator(tmpdir)
            generator.model = SequenceModel([INVALID_REPORT_JSON, VALID_REPORT_JSON])

            report = generator.generate()

            self.assertEqual(report["report_title"], "Coding Agent Engineering Inflection Point")
            self.assertEqual(len(generator.model.prompts), 2)
            raw_attempt1 = Path(generator.save_dir) / "report_raw_attempt1.txt"
            self.assertTrue(raw_attempt1.exists())
            self.assertIn('from "prototype" to "production"', raw_attempt1.read_text(encoding="utf-8"))
            self.assertFalse((Path(generator.save_dir) / "report_raw_attempt2.txt").exists())

    def test_generate_raises_after_second_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = self.make_generator(tmpdir)
            generator.model = SequenceModel([INVALID_REPORT_JSON, INVALID_REPORT_JSON])

            with self.assertRaises(ValueError) as exc_info:
                generator.generate()

            message = str(exc_info.exception)
            self.assertIn("report_raw_attempt1.txt", message)
            self.assertIn("report_raw_attempt2.txt", message)
            self.assertTrue((Path(generator.save_dir) / "report_raw_attempt1.txt").exists())
            self.assertTrue((Path(generator.save_dir) / "report_raw_attempt2.txt").exists())
            self.assertEqual(len(generator.model.prompts), 2)

    def test_generate_success_without_retry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = self.make_generator(tmpdir)
            generator.model = SequenceModel([VALID_REPORT_JSON])

            report = generator.generate()

            self.assertEqual(report["report_title"], "Coding Agent Engineering Inflection Point")
            self.assertEqual(len(generator.model.prompts), 1)
            self.assertFalse((Path(generator.save_dir) / "report_raw_attempt1.txt").exists())
            self.assertFalse((Path(generator.save_dir) / "report_raw_attempt2.txt").exists())


if __name__ == "__main__":
    unittest.main()
