"""
📊 quant.py — The Quant
=========================
Cold mathematical analyst that writes and executes Python code
for Monte Carlo simulations and financial calculations.
"""

import re
from brain import AgentAnalysis
from prompts.system_prompts import QUANT_PROMPT, DEFENSE_PROMPT, WEIGH_IN_PROMPT
from tools.code_executor import execute_python_code, extract_numeric_results


class Quant:
    """The Quant — runs Monte Carlo simulations and financial models."""

    NAME = "quant"
    ROLE = "Financial Analyst (The Quant)"

    def __init__(self, llm_provider):
        self.llm = llm_provider

    def analyze(self, idea: dict, **kwargs) -> AgentAnalysis:
        """
        Run financial analysis on the business idea.
        1. Ask LLM to write Monte Carlo simulation code
        2. Execute that code
        3. Combine code results with LLM analysis

        Args:
            idea: Dict with description, budget, target_market, etc.

        Returns:
            AgentAnalysis with financial data and success probability
        """
        # --- Step 1: Ask the LLM to write simulation code ---
        prompt = self._build_prompt(idea)

        response = self.llm.call(
            agent_name=self.NAME,
            user_message=prompt,
            system_prompt=QUANT_PROMPT,
            temperature=0.3,  # Low temperature for precise code
            max_tokens=3000,
        )

        # --- Step 2: Extract Python code from the response ---
        code = self._extract_code(response)

        # --- Step 3: Execute the code ---
        financial_data = {}
        code_output = ""

        if code:
            exec_result = execute_python_code(code)

            if exec_result["success"]:
                financial_data = extract_numeric_results(exec_result)
                code_output = exec_result["output"]
                print(f"  📊 Quant code executed successfully!")
                print(f"     {code_output[:200]}")
            else:
                print(f"  ⚠️  Quant code failed: {exec_result['error'][:200]}")
                # Try a fallback with simpler calculations
                financial_data = self._fallback_calculation(idea)
                code_output = "Code execution failed. Used fallback estimates."
        else:
            print("  ⚠️  No code found in Quant response. Using fallback.")
            financial_data = self._fallback_calculation(idea)
            code_output = "No code generated. Used fallback estimates."

        # --- Step 4: Build the analysis ---
        score = self._extract_score(response)

        # Adjust score based on actual Monte Carlo results
        success_prob = financial_data.get("success_probability", 0.5)
        if isinstance(success_prob, (int, float)):
            # Blend LLM score with Monte Carlo result
            score = (score * 0.4) + (success_prob * 10 * 0.6)

        risks = []
        if financial_data.get("worst_case", 0) < 0:
            risks.append(
                f"Worst-case scenario shows loss: ${financial_data['worst_case']:,.0f}"
            )
        if success_prob < 0.5:
            risks.append(
                f"Monte Carlo shows only {success_prob:.0%} success probability"
            )

        strengths = []
        if success_prob > 0.7:
            strengths.append(
                f"High success probability: {success_prob:.0%}"
            )
        if financial_data.get("roi", 0) > 50:
            strengths.append(
                f"Strong ROI: {financial_data['roi']:.1f}%"
            )

        # Include code in the analysis text
        full_analysis = (
            f"{response}\n\n"
            f"--- CODE EXECUTION RESULTS ---\n"
            f"{code_output}\n"
        )

        return AgentAnalysis(
            agent_name=self.NAME,
            role=self.ROLE,
            analysis=full_analysis,
            score=round(score, 1),
            key_risks=risks,
            key_strengths=strengths,
            raw_data=financial_data,
        )

    def defend(self, context: dict) -> str:
        """Defend financial analysis with numbers."""
        prompt = DEFENSE_PROMPT.format(
            agent_name="THE QUANT (Financial Analyst)",
            challenge=context.get("challenge", ""),
            my_analysis=context.get("my_analysis", "")[:500],
        )
        return self.llm.call(
            agent_name=self.NAME,
            user_message=prompt,
            temperature=0.3,
            max_tokens=300,
        )

    def weigh_in(self, context: dict) -> str:
        """Give mathematical opinion on the debate."""
        prompt = WEIGH_IN_PROMPT.format(
            agent_name="THE QUANT (Financial Analyst)",
            challenger=context.get("challenger", ""),
            defender=context.get("defender", ""),
            challenge=context.get("challenge", "")[:300],
            defense=context.get("defense", "")[:300],
        )
        return self.llm.call(
            agent_name=self.NAME,
            user_message=prompt,
            temperature=0.3,
            max_tokens=200,
        )

    # --- Helpers ---

    def _build_prompt(self, idea: dict) -> str:
        """Build a detailed prompt with financial data for the LLM."""
        budget = idea.get("budget", 50000)
        parts = [
            f"BUSINESS IDEA: {idea.get('description', 'Unknown')}",
            f"INITIAL INVESTMENT: ${budget:,}",
            f"TARGET MARKET: {idea.get('target_market', 'Unknown')}",
            f"REVENUE MODEL: {idea.get('revenue_model', 'Unknown')}",
            "",
            "Write Python code for a Monte Carlo simulation with 1000 scenarios.",
            f"Use ${budget:,} as the initial investment.",
            "Make reasonable assumptions for revenue and cost ranges.",
            "You MUST define all required variables (success_probability, mean_profit, etc.)",
        ]
        return "\n".join(parts)

    def _extract_code(self, text: str) -> str:
        """Extract Python code from the LLM response (from code blocks)."""
        # Look for ```python ... ``` blocks
        pattern = r"```python\s*\n(.*?)```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()

        # Fallback: look for ``` ... ``` blocks
        pattern = r"```\s*\n(.*?)```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            code = match.group(1).strip()
            if "import" in code or "def " in code or "for " in code:
                return code

        return ""

    def _extract_score(self, text: str) -> float:
        """Extract confidence score from response."""
        patterns = [
            r"(?:confidence|score|rating)[:\s]*(\d+(?:\.\d+)?)\s*/?\s*10",
            r"(\d+(?:\.\d+)?)\s*/\s*10",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return min(max(float(match.group(1)), 0.0), 10.0)
        return 5.0

    def _fallback_calculation(self, idea: dict) -> dict:
        """Simple fallback if code execution fails."""
        import random
        import numpy as np

        budget = idea.get("budget", 50000)
        n = 1000
        profits = []
        for _ in range(n):
            revenue = random.gauss(budget * 2, budget * 0.5)
            costs = random.gauss(budget * 1.2, budget * 0.3)
            profits.append(revenue - costs)

        profits = np.array(profits)
        return {
            "success_probability": float(np.sum(profits > 0) / n),
            "mean_profit": float(np.mean(profits)),
            "median_profit": float(np.median(profits)),
            "worst_case": float(np.percentile(profits, 5)),
            "best_case": float(np.percentile(profits, 95)),
            "std_deviation": float(np.std(profits)),
            "roi": float((np.mean(profits) / budget) * 100),
            "break_even_months": max(1, int(budget / max(np.mean(profits) / 12, 1))),
            "_note": "Fallback calculation — LLM code execution failed",
        }
