import unittest
from unittest.mock import patch

from orchestrator import orchestrate_goal


class OrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.env_patcher = patch.dict("os.environ", {"OPENAI_API_KEY": ""})
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()

    def test_mvp_launch_goal_returns_meaningful_plan(self):
        result = orchestrate_goal("Составь план запуска MVP")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["goal"], "Составь план запуска MVP")
        self.assertEqual(result["primary_role"], "planner")
        self.assertIn("planner", result["used_roles"])
        self.assertIn("researcher", result["used_roles"])
        self.assertIn("builder", result["used_roles"])
        self.assertIn("reviewer", result["used_roles"])
        self.assertGreaterEqual(len(result["phases"]), 3)
        self.assertGreaterEqual(len(result["risks"]), 1)
        self.assertGreaterEqual(len(result["next_actions"]), 3)
        self.assertNotIn("Stub orchestrator accepted the goal", str(result))

    def test_result_shape_is_stable(self):
        result = orchestrate_goal("Составь план запуска MVP")

        expected_keys = {
            "status",
            "goal",
            "summary",
            "primary_role",
            "used_roles",
            "owner_roles",
            "phases",
            "risks",
            "next_actions",
            "agent_outputs",
            "routing_reason",
        }

        self.assertEqual(set(result.keys()), expected_keys)
        self.assertIsInstance(result["phases"], list)
        self.assertIsInstance(result["risks"], list)
        self.assertIsInstance(result["next_actions"], list)
        self.assertIsInstance(result["owner_roles"], dict)
        self.assertIsInstance(result["agent_outputs"], dict)


if __name__ == "__main__":
    unittest.main()
