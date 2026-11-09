from bughound_agent import BugHoundAgent
from llm_client import MockClient


def test_workflow_runs_in_offline_mode_and_returns_shape():
    agent = BugHoundAgent(client=None)  # heuristic-only
    code = "def f():\n    print('hi')\n    return True\n"
    result = agent.run(code)

    assert isinstance(result, dict)
    assert "issues" in result
    assert "fixed_code" in result
    assert "risk" in result
    assert "logs" in result

    assert isinstance(result["issues"], list)
    assert isinstance(result["fixed_code"], str)
    assert isinstance(result["risk"], dict)
    assert isinstance(result["logs"], list)
    assert len(result["logs"]) > 0


def test_offline_mode_detects_print_issue():
    agent = BugHoundAgent(client=None)
    code = "def f():\n    print('hi')\n    return True\n"
    result = agent.run(code)

    assert any(issue.get("type") == "Code Quality" for issue in result["issues"])


def test_offline_mode_proposes_logging_fix_for_print():
    agent = BugHoundAgent(client=None)
    code = "def f():\n    print('hi')\n    return True\n"
    result = agent.run(code)

    fixed = result["fixed_code"]
    assert "logging" in fixed
    assert "logging.info(" in fixed


def test_offline_medium_severity_issue_does_not_auto_fix():
    agent = BugHoundAgent(client=None)
    code = "# TODO: finish this function\n\ndef f():\n    return 1\n"

    result = agent.run(code)

    assert result["risk"]["score"] == 80
    assert result["risk"]["level"] == "low"
    assert result["risk"]["should_autofix"] is False


def test_mock_client_forces_llm_fallback_to_heuristics_for_analysis():
    # MockClient returns non-JSON for analyzer prompts, so agent should fall back.
    agent = BugHoundAgent(client=MockClient())
    code = "def f():\n    print('hi')\n    return True\n"
    result = agent.run(code)

    assert any(issue.get("type") == "Code Quality" for issue in result["issues"])
    # Ensure we logged the fallback path
    assert any("Falling back to heuristics" in entry.get("message", "") for entry in result["logs"])


def test_invalid_llm_severity_falls_back_to_heuristics():
    class InvalidSeverityClient:
        def complete(self, system_prompt, user_prompt):
            return '[{"type":"Reliability","severity":"Critical","msg":"Bare except may hide errors."}]'

    agent = BugHoundAgent(client=InvalidSeverityClient())
    code = "def f():\n    try:\n        return 1\n    except:\n        return 0\n"

    issues = agent.analyze(code)

    assert issues == [
        {
            "type": "Reliability",
            "severity": "High",
            "msg": "Found a bare `except:`. Catch a specific exception or use `except Exception as e:`.",
        }
    ]
    assert any("Falling back to heuristics" in entry["message"] for entry in agent.logs)


def test_mock_client_fixer_falls_back_on_comment_only_output():
    agent = BugHoundAgent(client=MockClient())
    code = "def f():\n    print('hi')\n    return True\n"
    result = agent.run(code)

    assert "MockClient: no rewrite available" not in result["fixed_code"]
    assert any(
        "falling back to heuristic fixer" in entry.get("message", "").lower()
        for entry in result["logs"]
    )
    assert "logging.info(" in result["fixed_code"] or "import logging" in result["fixed_code"]
