import unittest
from unittest.mock import patch

from fastmcp import Client

from server import handle_run_orchestrator, mcp


class ServerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.env_patcher = patch.dict("os.environ", {"OPENAI_API_KEY": ""})
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()

    async def test_mcp_tool_is_registered(self):
        async with Client(mcp) as client:
            tools = await client.list_tools()

        self.assertIn("run_orchestrator", [tool.name for tool in tools])

    async def test_mcp_tool_call_returns_orchestration_result(self):
        async with Client(mcp) as client:
            result = await client.call_tool(
                "run_orchestrator",
                {"goal": "Create an MVP launch plan"},
            )

        data = result.structured_content

        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["primary_role"], "planner")
        self.assertIn("summary", data)
        self.assertIn("phases", data)
        self.assertIn("risks", data)
        self.assertIn("next_actions", data)
        self.assertNotIn("Stub orchestrator accepted the goal", str(data))

    def test_direct_tool_call_rejects_empty_goal(self):
        result = handle_run_orchestrator("   ")

        self.assertEqual(result["status"], "error")
        self.assertIn("goal", result["message"].lower())


if __name__ == "__main__":
    unittest.main()
