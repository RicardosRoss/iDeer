import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import CommonConfig, LLMConfig
from idea_generator import IdeaGenerator


class DummyModel:
    def __init__(self, response: str):
        self.response = response
        self.last_prompt = None

    def inference(self, prompt, temperature=0.7):
        self.last_prompt = prompt
        return self.response


def load_sample_recommendations(date: str = "2026-03-06") -> dict[str, list[dict]]:
    history_dir = ROOT / "history"
    all_recs = {}
    for source in ("github", "huggingface", "twitter"):
        json_dir = history_dir / source / date / "json"
        source_items = []
        for json_file in sorted(json_dir.glob("*.json"))[:8]:
            with open(json_file, "r", encoding="utf-8") as f:
                source_items.append(json.load(f))
        all_recs[source] = source_items
    return all_recs


class IdeaGeneratorTest(unittest.TestCase):
    def setUp(self):
        self.all_recs = load_sample_recommendations()
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
        self.generator = IdeaGenerator(
            all_recs=self.all_recs,
            profile_path=str(ROOT / "profiles" / "researcher_profile.md"),
            llm_config=self.llm_config,
            common_config=self.common_config,
            min_score=7,
            max_items=6,
            idea_count=3,
        )

    def test_filter_items_keeps_high_scores_and_diversity(self):
        filtered = self.generator._filter_items(self.all_recs)

        self.assertLessEqual(len(filtered), 6)
        self.assertTrue(all(item["score"] >= 7 for item in filtered))
        self.assertGreaterEqual(len({item["_source"] for item in filtered}), 2)

    def test_generate_normalizes_llm_output(self):
        self.generator.model = DummyModel(
            """```json
            [
              {
                "title": "代理记忆安全基准",
                "research_direction": "Benchmark agent memory editing under adversarial task drift",
                "hypothesis": "如果显式建模记忆写入与安全冲突，Agent 的长程任务鲁棒性会更高",
                "hypothesis_en": "Explicitly modeling the conflict between memory writes and safety constraints improves long-horizon robustness.",
                "inspired_by": [
                  {"title": "agentscope-ai/ReMe", "source": "github", "url": "https://github.com/agentscope-ai/ReMe"}
                ],
                "connects_to_project": "ATbench_Engine",
                "interest_area": "Safety",
                "novelty_estimate": "medium",
                "feasibility": "high",
                "composite_score": "8.7",
                "min_experiment": "在 ATbench_Engine 上加入记忆污染与任务漂移设置，比较带约束与不带约束的记忆模块。"
              }
            ]
            ```"""
        )

        ideas = self.generator.generate()

        self.assertEqual(len(ideas), 1)
        self.assertEqual(ideas[0]["id"], f"idea-{self.generator.run_date}-001")
        self.assertEqual(ideas[0]["novelty_estimate"], "MEDIUM")
        self.assertEqual(ideas[0]["feasibility"], "HIGH")
        self.assertEqual(ideas[0]["composite_score"], 8.7)
        self.assertIn("ATbench_Engine", ideas[0]["connects_to_project"])

    def test_save_and_render_email_write_artifacts(self):
        ideas = [
            {
                "id": "idea-2026-03-06-001",
                "title": "代理记忆安全基准",
                "title_en": "Agent Memory Safety Benchmark",
                "research_direction": "Benchmark agent memory editing under adversarial task drift",
                "hypothesis": "如果显式建模记忆写入与安全冲突，Agent 的长程任务鲁棒性会更高",
                "hypothesis_en": "Explicitly modeling the conflict between memory writes and safety constraints improves long-horizon robustness.",
                "inspired_by": [
                    {
                        "title": "agentscope-ai/ReMe",
                        "source": "github",
                        "url": "https://github.com/agentscope-ai/ReMe",
                    }
                ],
                "connects_to_project": "ATbench_Engine",
                "interest_area": "Safety",
                "novelty_estimate": "MEDIUM",
                "feasibility": "HIGH",
                "composite_score": 8.7,
                "min_experiment": "在 ATbench_Engine 上加入记忆污染与任务漂移设置。",
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            self.generator.save_dir = tmpdir
            self.generator.email_cache_path = str(Path(tmpdir) / "ideas_email.html")

            self.generator.save(ideas)
            html = self.generator.render_email(ideas)

            self.assertTrue((Path(tmpdir) / "ideas.json").exists())
            self.assertTrue((Path(tmpdir) / "ideas.md").exists())
            self.assertTrue((Path(tmpdir) / "ideas_email.html").exists())
            self.assertIn("/idea-from-daily", html)


if __name__ == "__main__":
    unittest.main()
