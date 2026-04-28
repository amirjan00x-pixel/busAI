"""
⚔️ executioner.py — The Executioner
======================================
The most ruthless critic in the war room.
Receives all other agents' analyses and tears them apart.
Default position: the idea WILL fail.
"""

import re
from brain import AgentAnalysis
from prompts.system_prompts import (
    EXECUTIONER_PROMPT,
    CHALLENGE_PROMPT,
    DEFENSE_PROMPT,
    WEIGH_IN_PROMPT,
)


class Executioner:
    """The Executioner — ruthless critic that tries to kill weak ideas."""

    NAME = "executioner"
    ROLE = "Critical Analyst (The Executioner)"

    def __init__(self, llm_provider):
        self.llm = llm_provider

    def analyze(self, idea: dict, prior_analyses: list = None, **kwargs) -> AgentAnalysis:
        """
        Receive all prior analyses and write a death-or-survival verdict.

        Args:
            idea: The business idea dict
            prior_analyses: List of AgentAnalysis from the other 3 agents

        Returns:
            AgentAnalysis with the Executioner's brutal assessment
        """
        prior_analyses = prior_analyses or []

        # --- Build the evidence packet ---
        evidence = self._compile_evidence(idea, prior_analyses)

        response = self.llm.call(
            agent_name=self.NAME,
            user_message=evidence,
            system_prompt=EXECUTIONER_PROMPT,
            temperature=0.8,  # Higher temp for creative destruction
            max_tokens=2000,
        )

        score = self._extract_score(response)
        risks = self._extract_kill_shots(response)
        strengths = self._extract_survivability(response)

        return AgentAnalysis(
            agent_name=self.NAME,
            role=self.ROLE,
            analysis=response,
            score=score,
            key_risks=risks,
            key_strengths=strengths,
        )

    def challenge(self, context: dict) -> str:
        """
        Generate a targeted challenge against another agent's analysis.
        Used during the debate phase.

        Args:
            context: Dict with target_agent, target_analysis, target_score, etc.
        """
        # Format debate history
        history = context.get("debate_history", [])
        history_text = ""
        if history:
            history_text = "\n".join(
                f"- {m['sender']}: {m['content'][:100]}" for m in history[-5:]
            )

        prompt = CHALLENGE_PROMPT.format(
            target_agent=context.get("target_agent", "Unknown"),
            target_analysis=context.get("target_analysis", "")[:800],
            target_score=context.get("target_score", "?"),
            debate_history=history_text or "No prior debate.",
        )

        return self.llm.call(
            agent_name=self.NAME,
            user_message=prompt,
            system_prompt=EXECUTIONER_PROMPT,
            temperature=0.8,
            max_tokens=300,
        )

    def defend(self, context: dict) -> str:
        """
        Even the Executioner can be challenged (by consensus logic).
        Defends position when other agents push back.
        """
        prompt = DEFENSE_PROMPT.format(
            agent_name="THE EXECUTIONER",
            challenge=context.get("challenge", ""),
            my_analysis=context.get("my_analysis", "")[:500],
        )
        return self.llm.call(
            agent_name=self.NAME,
            user_message=prompt,
            temperature=0.7,
            max_tokens=300,
        )

    def weigh_in(self, context: dict) -> str:
        """The Executioner weighs in on someone else's debate."""
        prompt = WEIGH_IN_PROMPT.format(
            agent_name="THE EXECUTIONER",
            challenger=context.get("challenger", ""),
            defender=context.get("defender", ""),
            challenge=context.get("challenge", "")[:300],
            defense=context.get("defense", "")[:300],
        )
        return self.llm.call(
            agent_name=self.NAME,
            user_message=prompt,
            temperature=0.7,
            max_tokens=200,
        )

    # --- Helpers ---

    def _compile_evidence(self, idea: dict, analyses: list) -> str:
        """Compile all prior analyses into one evidence packet for the Executioner."""
        parts = [
            f"=== BUSINESS IDEA ===",
            f"{idea.get('description', 'Unknown')}",
            f"Budget: ${idea.get('budget', 'Unknown'):,}" if isinstance(idea.get('budget'), (int, float)) else "",
            f"Market: {idea.get('target_market', 'Unknown')}",
            "",
        ]

        for analysis in analyses:
            parts.append(f"=== {analysis.role.upper()} (Score: {analysis.score}/10) ===")
            # Truncate to keep context window manageable
            parts.append(analysis.analysis[:1000])
            if analysis.key_risks:
                parts.append("RISKS: " + " | ".join(analysis.key_risks[:3]))
            if analysis.key_strengths:
                parts.append("STRENGTHS: " + " | ".join(analysis.key_strengths[:3]))
            if analysis.raw_data:
                # Include key financial metrics
                for key in ["success_probability", "roi", "mean_profit", "worst_case"]:
                    if key in analysis.raw_data:
                        parts.append(f"  {key}: {analysis.raw_data[key]}")
            parts.append("")

        parts.append(
            "YOUR MISSION: Tear apart ALL of the above. "
            "Find the fatal flaws. Write the death-or-survival verdict."
        )

        return "\n".join(parts)

    def _extract_score(self, text: str) -> float:
        """Extract survivability rating."""
        patterns = [
            r"(?:survivability|rating|score)[:\s]*(\d+(?:\.\d+)?)\s*/?\s*10",
            r"(\d+(?:\.\d+)?)\s*/\s*10",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return min(max(float(match.group(1)), 0.0), 10.0)
        return 4.0  # Executioner defaults to pessimistic

    def _extract_kill_shots(self, text: str) -> list[str]:
        """Extract the top reasons the idea will fail."""
        lines = text.split("\n")
        results = []
        capture = False
        for line in lines:
            if re.search(r"kill\s*shot|fail|fatal|death|flaw", line, re.IGNORECASE):
                capture = True
                # Check if the header line itself contains the point
                stripped = line.strip().lstrip("-*•123456789. #")
                if stripped and len(stripped) > 15 and ":" not in stripped[:5]:
                    results.append(stripped)
                continue
            if capture:
                stripped = line.strip().lstrip("-*•123456789. ")
                if stripped and len(stripped) > 10:
                    results.append(stripped)
                if len(results) >= 5 or (not stripped and results):
                    break
        return results[:5]

    def _extract_survivability(self, text: str) -> list[str]:
        """Extract any strengths the Executioner grudgingly admits."""
        lines = text.split("\n")
        results = []
        for line in lines:
            if re.search(r"surviv|grudging|acknowledge|strong|worthy", line, re.IGNORECASE):
                stripped = line.strip().lstrip("-*•123456789. ")
                if stripped and len(stripped) > 10:
                    results.append(stripped)
        return results[:3]
