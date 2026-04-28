"""
🧠 strategist.py — The Visionary
==================================
Transforms raw business ideas into structured business models.
Uses frameworks like Business Model Canvas to produce actionable output.
"""

import json
import re
from brain import AgentAnalysis
from prompts.system_prompts import STRATEGIST_PROMPT, DEFENSE_PROMPT, WEIGH_IN_PROMPT


class Strategist:
    """The Visionary — converts ideas into business models."""

    NAME = "strategist"
    ROLE = "Business Strategist (The Visionary)"

    def __init__(self, llm_provider):
        self.llm = llm_provider

    def analyze(self, idea: dict, **kwargs) -> AgentAnalysis:
        """
        Analyze a business idea and produce a structured business model.

        Args:
            idea: Dict with description, budget, target_market, etc.

        Returns:
            AgentAnalysis with the business model and confidence score
        """
        # Build the prompt with idea details
        idea_text = self._format_idea(idea)

        # Check if this is a revision cycle
        revision_feedback = idea.get("_revision_feedback", [])
        if revision_feedback:
            idea_text += (
                "\n\n⚠️ REVISION CYCLE — The Executioner found these issues "
                "in the previous round. Address them:\n"
                + "\n".join(f"- {fb}" for fb in revision_feedback)
            )

        response = self.llm.call(
            agent_name=self.NAME,
            user_message=idea_text,
            system_prompt=STRATEGIST_PROMPT,
            temperature=0.7,
            max_tokens=2000,
        )

        # Extract score from response
        score = self._extract_score(response)

        # Extract risks and strengths
        risks = self._extract_section(response, "risk")
        strengths = self._extract_section(response, "advantage|strength|value")

        return AgentAnalysis(
            agent_name=self.NAME,
            role=self.ROLE,
            analysis=response,
            score=score,
            key_risks=risks,
            key_strengths=strengths,
        )

    def defend(self, context: dict) -> str:
        """Defend position when challenged by the Executioner."""
        prompt = DEFENSE_PROMPT.format(
            agent_name="THE VISIONARY (Strategist)",
            challenge=context.get("challenge", ""),
            my_analysis=context.get("my_analysis", "")[:500],
        )
        return self.llm.call(
            agent_name=self.NAME,
            user_message=prompt,
            temperature=0.6,
            max_tokens=300,
        )

    def weigh_in(self, context: dict) -> str:
        """Give opinion on an ongoing debate between other agents."""
        prompt = WEIGH_IN_PROMPT.format(
            agent_name="THE VISIONARY (Strategist)",
            challenger=context.get("challenger", ""),
            defender=context.get("defender", ""),
            challenge=context.get("challenge", "")[:300],
            defense=context.get("defense", "")[:300],
        )
        return self.llm.call(
            agent_name=self.NAME,
            user_message=prompt,
            temperature=0.5,
            max_tokens=200,
        )

    # --- Helpers ---

    def _format_idea(self, idea: dict) -> str:
        """Format the idea dict into a readable prompt."""
        parts = [f"BUSINESS IDEA: {idea.get('description', 'No description')}"]
        if idea.get("budget"):
            parts.append(f"BUDGET: ${idea['budget']:,}")
        if idea.get("target_market"):
            parts.append(f"TARGET MARKET: {idea['target_market']}")
        if idea.get("revenue_model"):
            parts.append(f"REVENUE MODEL: {idea['revenue_model']}")
        if idea.get("competitors"):
            parts.append(f"KNOWN COMPETITORS: {', '.join(idea['competitors'])}")
        return "\n".join(parts)

    def _extract_score(self, text: str) -> float:
        """Extract the confidence score from LLM response."""
        patterns = [
            r"(?:confidence|score|rating)[:\s]*(\d+(?:\.\d+)?)\s*/?\s*10",
            r"(\d+(?:\.\d+)?)\s*/\s*10",
            r"(\d+(?:\.\d+)?)\s*out of\s*10",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                score = float(match.group(1))
                return min(max(score, 0.0), 10.0)
        return 5.0  # Default if no score found

    def _extract_section(self, text: str, keyword: str) -> list[str]:
        """Extract bullet points near a keyword in the response."""
        lines = text.split("\n")
        results = []
        capture = False
        for line in lines:
            if re.search(keyword, line, re.IGNORECASE):
                capture = True
                continue
            if capture:
                stripped = line.strip().lstrip("-*•123456789. ")
                if stripped and len(stripped) > 10:
                    results.append(stripped)
                if len(results) >= 5 or (not stripped and results):
                    break
        return results[:5]
