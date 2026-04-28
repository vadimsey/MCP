import unittest
from unittest.mock import patch

from orchestrator import get_openai_enabled_roles, orchestrate_goal, should_use_openai


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

    def test_openai_defaults_to_planner_only(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}, clear=True):
            self.assertEqual(get_openai_enabled_roles(), {"planner"})
            self.assertTrue(should_use_openai("planner"))
            self.assertFalse(should_use_openai("researcher"))
            self.assertFalse(should_use_openai("builder"))
            self.assertFalse(should_use_openai("reviewer"))

    def test_openai_enabled_roles_can_be_configured(self):
        with patch.dict(
            "os.environ",
            {
                "OPENAI_API_KEY": "test-key",
                "OPENAI_ENABLED_ROLES": "planner,reviewer",
            },
            clear=True,
        ):
            self.assertEqual(get_openai_enabled_roles(), {"planner", "reviewer"})
            self.assertTrue(should_use_openai("planner"))
            self.assertFalse(should_use_openai("researcher"))
            self.assertFalse(should_use_openai("builder"))
            self.assertTrue(should_use_openai("reviewer"))


if __name__ == "__main__":
    unittest.main()
