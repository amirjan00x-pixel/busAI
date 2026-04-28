"""
🔍 researcher.py — The Spy
============================
Market intelligence operative that searches the web for competitors,
market failures, and hidden threats using DuckDuckGo.
"""

import re
from brain import AgentAnalysis
from prompts.system_prompts import RESEARCHER_PROMPT, DEFENSE_PROMPT, WEIGH_IN_PROMPT
from tools.search_tool import search_web, format_search_results


class Researcher:
    """The Spy — hunts for market intelligence and competitor data."""

    NAME = "researcher"
    ROLE = "Market Researcher (The Spy)"

    def __init__(self, llm_provider):
        self.llm = llm_provider

    def analyze(self, idea: dict, **kwargs) -> AgentAnalysis:
        """
        Research the market for the given business idea.
        Performs web searches, then asks the LLM to analyze findings.

        Args:
            idea: Dict with description, target_market, competitors, etc.

        Returns:
            AgentAnalysis with market intelligence
        """
        description = idea.get("description", "")

        # --- Step 1: Generate smart search queries ---
        queries = self._generate_queries(description, idea)

        # --- Step 2: Execute searches ---
        all_results = []
        for query in queries:
            results = search_web(query, max_results=3)
            all_results.extend(results)

        search_text = format_search_results(all_results)

        # --- Step 3: Ask LLM to analyze the search results ---
        prompt = (
            f"BUSINESS IDEA: {description}\n\n"
            f"TARGET MARKET: {idea.get('target_market', 'Unknown')}\n\n"
            f"KNOWN COMPETITORS: {', '.join(idea.get('competitors', ['None listed']))}\n\n"
            f"--- WEB SEARCH RESULTS ---\n\n"
            f"{search_text}\n\n"
            f"--- END OF SEARCH RESULTS ---\n\n"
            f"Analyze these findings according to your mission."
        )

        response = self.llm.call(
            agent_name=self.NAME,
            user_message=prompt,
            system_prompt=RESEARCHER_PROMPT,
            temperature=0.5,
            max_tokens=2000,
        )

        score = self._extract_score(response)
        risks = self._extract_bullets(response, "threat|risk|failure|hidden")
        strengths = self._extract_bullets(response, "success|opportunity|growth")

        return AgentAnalysis(
            agent_name=self.NAME,
            role=self.ROLE,
            analysis=response,
            score=score,
            key_risks=risks,
            key_strengths=strengths,
            raw_data={"search_results": all_results, "queries_used": queries},
        )

    def defend(self, context: dict) -> str:
        """Defend research findings when challenged."""
        prompt = DEFENSE_PROMPT.format(
            agent_name="THE SPY (Market Researcher)",
            challenge=context.get("challenge", ""),
            my_analysis=context.get("my_analysis", "")[:500],
        )
        return self.llm.call(
            agent_name=self.NAME,
            user_message=prompt,
            temperature=0.5,
            max_tokens=300,
        )

    def weigh_in(self, context: dict) -> str:
        """Give opinion on an ongoing debate."""
        prompt = WEIGH_IN_PROMPT.format(
            agent_name="THE SPY (Market Researcher)",
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

    def _generate_queries(self, description: str, idea: dict) -> list[str]:
        """Generate targeted search queries based on the business idea."""
        queries = [
            f"{description} startup failure",
            f"{description} market size revenue",
            f"{description} competitors analysis",
        ]
        target = idea.get("target_market", "")
        if target:
            queries.append(f"{description} {target} demand")
        return queries[:4]  # Max 4 queries to keep it fast

    def _extract_score(self, text: str) -> float:
        """Extract confidence score from LLM response."""
        patterns = [
            r"(?:confidence|score|rating)[:\s]*(\d+(?:\.\d+)?)\s*/?\s*10",
            r"(\d+(?:\.\d+)?)\s*/\s*10",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return min(max(float(match.group(1)), 0.0), 10.0)
        return 5.0

    def _extract_bullets(self, text: str, keyword: str) -> list[str]:
        """Extract bullet points near a keyword."""
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
