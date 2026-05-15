from __future__ import annotations

from iperson.agent.engine import DigitalTwinAgent


class TestDigitalTwinAgent:
    def test_agent_initialization(self) -> None:
        agent = DigitalTwinAgent({"platform": "wechat"})
        assert agent.config["platform"] == "wechat"

    def test_agent_defaults(self) -> None:
        agent = DigitalTwinAgent()
        assert agent.default_persona == "default"