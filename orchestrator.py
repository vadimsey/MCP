from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AgentRole:
    name: str
    purpose: str
    keywords: tuple[str, ...]


AGENT_ROLES: dict[str, AgentRole] = {
    "planner": AgentRole(
        name="planner",
        purpose="Break the goal into a practical strategy, phases, and next actions.",
        keywords=(
            "plan",
            "planning",
            "strategy",
            "roadmap",
            "mvp",
            "launch",
            "план",
            "стратег",
            "roadmap",
            "mvp",
            "мвп",
            "запуск",
        ),
    ),
    "researcher": AgentRole(
        name="researcher",
        purpose="Identify assumptions, missing information, market context, and analysis tasks.",
        keywords=(
            "research",
            "analysis",
            "analyze",
            "market",
            "competitor",
            "исслед",
            "анализ",
            "рынок",
            "конкур",
            "сравн",
        ),
    ),
    "builder": AgentRole(
        name="builder",
        purpose="Turn the goal into implementation tasks, code work, and delivery steps.",
        keywords=(
            "build",
            "code",
            "implement",
            "develop",
            "создай",
            "сделай",
            "код",
            "реализ",
            "разработ",
            "интеграц",
        ),
    ),
    "reviewer": AgentRole(
        name="reviewer",
        purpose="Check risks, quality gates, edge cases, and validation steps.",
        keywords=(
            "review",
            "risk",
            "audit",
            "check",
            "test",
            "проверк",
            "ревью",
            "риск",
            "аудит",
            "тест",
        ),
    ),
}


def orchestrate_goal(goal: str) -> dict[str, Any]:
    clean_goal = goal.strip()
    selected_roles = route_goal(clean_goal)
    primary_role = selected_roles[0]

    agent_outputs = {
        role_name: run_role_agent(role_name, clean_goal) for role_name in selected_roles
    }

    result = {
        "status": "ok",
        "goal": clean_goal,
        "summary": build_summary(clean_goal, primary_role),
        "primary_role": primary_role,
        "used_roles": selected_roles,
        "owner_roles": build_owner_roles(selected_roles),
        "phases": build_phases(clean_goal, agent_outputs),
        "risks": build_risks(clean_goal, agent_outputs),
        "next_actions": build_next_actions(clean_goal, agent_outputs),
        "agent_outputs": agent_outputs,
        "routing_reason": build_routing_reason(clean_goal, selected_roles),
    }

    return result


def route_goal(goal: str) -> list[str]:
    normalized_goal = goal.lower()
    matched_roles: list[str] = []

    for role_name, role in AGENT_ROLES.items():
        if any(keyword in normalized_goal for keyword in role.keywords):
            matched_roles.append(role_name)

    if not matched_roles:
        matched_roles.append("planner")

    if is_mvp_launch_goal(goal):
        for role_name in ("planner", "researcher", "builder", "reviewer"):
            if role_name not in matched_roles:
                matched_roles.append(role_name)

    if "planner" not in matched_roles:
        matched_roles.insert(0, "planner")

    if "reviewer" not in matched_roles:
        matched_roles.append("reviewer")

    return matched_roles


def run_role_agent(role_name: str, goal: str) -> dict[str, Any]:
    if role_name == "planner":
        return planner_agent(goal)
    if role_name == "researcher":
        return researcher_agent(goal)
    if role_name == "builder":
        return builder_agent(goal)
    if role_name == "reviewer":
        return reviewer_agent(goal)

    raise ValueError(f"Unknown agent role: {role_name}")


def should_use_openai() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def get_openai_model() -> str:
    return os.environ.get("OPENAI_MODEL", "gpt-5-mini")


def call_openai_role_agent(
    role_name: str,
    goal: str,
    output_hint: str,
) -> dict[str, Any] | None:
    if not should_use_openai():
        return None

    try:
        from openai import OpenAI

        role = AGENT_ROLES[role_name]
        client = OpenAI()
        response = client.responses.create(
            model=get_openai_model(),
            instructions=(
                f"You are the {role.name} agent in an MCP orchestration system. "
                f"Purpose: {role.purpose} "
                "Return practical, concise output for the orchestrator. "
                f"Expected focus: {output_hint}"
            ),
            input=goal,
        )

        return {
            "role": role_name,
            "backend": "openai_responses_api",
            "model": get_openai_model(),
            "focus": output_hint,
            "result": response.output_text,
        }
    except Exception as exc:
        return {
            "role": role_name,
            "backend": "rule_based",
            "focus": output_hint,
            "fallback_reason": f"OpenAI role call failed: {type(exc).__name__}",
        }


def planner_agent(goal: str) -> dict[str, Any]:
    openai_result = call_openai_role_agent(
        "planner",
        goal,
        "Strategy, phases, success metrics, and next actions.",
    )
    if openai_result and openai_result.get("backend") == "openai_responses_api":
        return openai_result

    if is_mvp_launch_goal(goal):
        result = {
            "role": "planner",
            "backend": "rule_based",
            "focus": "MVP launch plan",
            "recommendations": [
                "Define the target user, core problem, and one measurable MVP success metric.",
                "Reduce the scope to the smallest useful product that can be shipped and tested.",
                "Run a short launch cycle: validate, build, release, measure, then iterate.",
            ],
            "deliverables": [
                "MVP scope",
                "Launch roadmap",
                "Success metrics",
                "Post-launch iteration backlog",
            ],
        }
        if openai_result:
            result["fallback_reason"] = openai_result["fallback_reason"]
        return result

    result = {
        "role": "planner",
        "backend": "rule_based",
        "focus": "Goal decomposition",
        "recommendations": [
            "Clarify the desired outcome and acceptance criteria.",
            "Split the work into discovery, execution, validation, and iteration.",
            "Assign one owner role for each phase.",
        ],
        "deliverables": ["Work plan", "Milestones", "Acceptance criteria"],
    }
    if openai_result:
        result["fallback_reason"] = openai_result["fallback_reason"]
    return result


def researcher_agent(goal: str) -> dict[str, Any]:
    openai_result = call_openai_role_agent(
        "researcher",
        goal,
        "Assumptions, market context, missing information, and research questions.",
    )
    if openai_result and openai_result.get("backend") == "openai_responses_api":
        return openai_result

    result = {
        "role": "researcher",
        "backend": "rule_based",
        "focus": "Discovery and assumptions",
        "recommendations": [
            "List the key assumptions that must be true for the goal to succeed.",
            "Identify competitors, alternatives, or existing workflows users already use.",
            "Collect evidence before expanding scope.",
        ],
        "questions": [
            "Who is the first target user segment?",
            "What pain is urgent enough for users to try the MVP?",
            "Which metric proves the MVP is worth improving?",
        ],
    }
    if openai_result:
        result["fallback_reason"] = openai_result["fallback_reason"]
    return result


def builder_agent(goal: str) -> dict[str, Any]:
    openai_result = call_openai_role_agent(
        "builder",
        goal,
        "Implementation path, delivery tasks, integration points, and build risks.",
    )
    if openai_result and openai_result.get("backend") == "openai_responses_api":
        return openai_result

    result = {
        "role": "builder",
        "backend": "rule_based",
        "focus": "Implementation path",
        "recommendations": [
            "Build only the core workflow needed to test the main value proposition.",
            "Keep integrations and automation behind clear interfaces so they can be replaced later.",
            "Ship with basic logging and feedback collection from the first release.",
        ],
        "deliverables": [
            "Core user flow",
            "Deployment checklist",
            "Feedback capture mechanism",
        ],
    }
    if openai_result:
        result["fallback_reason"] = openai_result["fallback_reason"]
    return result


def reviewer_agent(goal: str) -> dict[str, Any]:
    openai_result = call_openai_role_agent(
        "reviewer",
        goal,
        "Risks, quality gates, validation checks, and review criteria.",
    )
    if openai_result and openai_result.get("backend") == "openai_responses_api":
        return openai_result

    result = {
        "role": "reviewer",
        "backend": "rule_based",
        "focus": "Risks and validation",
        "risks": [
            "Scope creep can delay the first useful release.",
            "Weak success metrics can make the MVP hard to evaluate.",
            "Skipping user feedback can produce a technically complete but unvalidated product.",
        ],
        "quality_gates": [
            "The MVP can be explained in one sentence.",
            "The first user flow works end to end.",
            "There is a clear decision rule for iterate, pivot, or stop.",
        ],
    }
    if openai_result:
        result["fallback_reason"] = openai_result["fallback_reason"]
    return result


def build_summary(goal: str, primary_role: str) -> str:
    if is_mvp_launch_goal(goal):
        return (
            "Prepared a practical MVP launch plan focused on validating the core "
            "user problem, shipping a small first version, measuring results, and "
            "iterating from real feedback."
        )

    return (
        f"Routed the goal to {primary_role} as the primary role and produced a "
        "practical execution outline with validation steps."
    )


def build_owner_roles(selected_roles: list[str]) -> dict[str, str]:
    return {
        role_name: AGENT_ROLES[role_name].purpose for role_name in selected_roles
    }


def build_phases(goal: str, agent_outputs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    if is_mvp_launch_goal(goal):
        return [
            {
                "name": "1. Define MVP",
                "owner_role": "planner",
                "output": "Target user, core pain, one key promise, and success metric.",
            },
            {
                "name": "2. Validate Demand",
                "owner_role": "researcher"
                if "researcher" in agent_outputs
                else "planner",
                "output": "Interview notes, competitor notes, and a clear go/no-go signal.",
            },
            {
                "name": "3. Build Core Flow",
                "owner_role": "builder" if "builder" in agent_outputs else "planner",
                "output": "Small working product that completes the main user workflow.",
            },
            {
                "name": "4. Launch Test",
                "owner_role": "planner",
                "output": "Release to a small audience, collect feedback, and measure activation.",
            },
            {
                "name": "5. Review and Iterate",
                "owner_role": "reviewer",
                "output": "Decision: improve, pivot, or stop based on metric and feedback.",
            },
        ]

    return [
        {
            "name": "1. Clarify",
            "owner_role": "planner",
            "output": "Goal, constraints, success criteria, and initial task list.",
        },
        {
            "name": "2. Execute",
            "owner_role": "builder" if "builder" in agent_outputs else "planner",
            "output": "Complete the smallest useful implementation or work product.",
        },
        {
            "name": "3. Validate",
            "owner_role": "reviewer",
            "output": "Check quality, risks, and whether the result satisfies the goal.",
        },
    ]


def build_risks(goal: str, agent_outputs: dict[str, dict[str, Any]]) -> list[str]:
    reviewer_risks = agent_outputs.get("reviewer", {}).get("risks", [])
    if reviewer_risks:
        return reviewer_risks

    if is_mvp_launch_goal(goal):
        return [
            "Scope creep can delay the first useful release.",
            "Weak success metrics can make the MVP hard to evaluate.",
            "Skipping user feedback can produce a technically complete but unvalidated product.",
        ]

    return [
        "Goal is underspecified.",
        "No explicit success metric is defined.",
        "Validation may be delayed until too late.",
    ]


def build_next_actions(goal: str, agent_outputs: dict[str, dict[str, Any]]) -> list[str]:
    if is_mvp_launch_goal(goal):
        return [
            "Write a one-sentence MVP promise for the first target user.",
            "Choose one success metric, for example first activation, paid intent, or retained usage.",
            "Cut the feature list to the smallest end-to-end workflow.",
            "Find 5-10 first users and schedule validation conversations.",
            "Set a launch date for a small private test.",
        ]

    return [
        "Clarify the expected output and deadline.",
        "Pick the primary owner role for execution.",
        "Run the first phase and review the result before expanding scope.",
    ]


def build_routing_reason(goal: str, selected_roles: list[str]) -> str:
    return (
        "Selected roles based on goal keywords and added planner/reviewer as "
        f"default orchestration roles. Roles: {', '.join(selected_roles)}."
    )


def is_mvp_launch_goal(goal: str) -> bool:
    normalized_goal = goal.lower()
    return any(
        keyword in normalized_goal
        for keyword in ("mvp", "мвп", "запуск", "launch", "roadmap")
    )
