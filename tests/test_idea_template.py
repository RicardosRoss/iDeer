import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from email_utils.idea_template import render_ideas_email


class IdeaTemplateTest(unittest.TestCase):
    def test_render_ideas_email_includes_date_and_command(self):
        html = render_ideas_email(
            ideas=[
                {
                    "id": "idea-2026-03-06-001",
                    "title": "代理记忆安全基准",
                    "hypothesis": "验证记忆写入约束是否提升长期安全性。",
                    "research_direction": "Benchmark agent memory editing under adversarial task drift",
                    "connects_to_project": "ATbench_Engine",
                    "interest_area": "Safety",
                    "novelty_estimate": "MEDIUM",
                    "feasibility": "HIGH",
                    "composite_score": 8.7,
                    "min_experiment": "在 ATbench_Engine 上加入记忆污染设置。",
                    "inspired_by": [
                        {
                            "title": "agentscope-ai/ReMe",
                            "source": "github",
                            "url": "https://github.com/agentscope-ai/ReMe",
                        }
                    ],
                }
            ],
            date="2026-03-06",
        )

        self.assertIn("Daily Research Ideas", html)
        self.assertIn("/idea-from-daily 2026-03-06 --idea 1", html)
        self.assertIn("2026-03-06", html)


if __name__ == "__main__":
    unittest.main()
