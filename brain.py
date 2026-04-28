"""
🧠 brain.py — The War Room Consensus Engine
=============================================
This is the central negotiation engine for The Iron Ledger.
It orchestrates 4 AI agents, manages debate rounds, detects consensus,
and produces a final strategic report with a numerical success probability.

Architecture:
    1. Each agent analyzes the business idea independently
    2. Agents enter a structured debate (max N rounds)
    3. The Executioner challenges every claim
    4. If critical flaws found → loop back to refine
    5. Consensus reached → generate final report with score
"""

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
#  Data Models
# ---------------------------------------------------------------------------

class Verdict(Enum):
    """Possible outcomes of the War Room deliberation."""
    APPROVED = "approved"           # Idea is viable — go ahead
    REJECTED = "rejected"           # Idea is fatally flawed
    NEEDS_REVISION = "needs_revision"  # Fixable issues found — loop back
    NO_CONSENSUS = "no_consensus"   # Agents couldn't agree


@dataclass
class AgentAnalysis:
    """One agent's analysis of the business idea."""
    agent_name: str
    role: str
    analysis: str               # The agent's full textual analysis
    score: float                # 0.0 to 10.0 — agent's confidence in the idea
    key_risks: list[str] = field(default_factory=list)
    key_strengths: list[str] = field(default_factory=list)
    raw_data: dict = field(default_factory=dict)  # Monte Carlo results, etc.


@dataclass
class DebateMessage:
    """A single message in the inter-agent debate."""
    sender: str                 # Agent name
    target: str                 # Who they're addressing ("all" or specific agent)
    content: str                # The argument
    message_type: str           # "challenge", "defense", "agreement", "rebuttal"
    round_number: int


@dataclass
class WarRoomReport:
    """The final deliverable to the user."""
    idea_summary: str
    verdict: Verdict
    final_score: float                          # 0.0–10.0
    success_probability: float                  # 0.0–1.0 (from Monte Carlo)
    risk_analysis: dict = field(default_factory=dict)
    agent_analyses: list[AgentAnalysis] = field(default_factory=list)
    debate_log: list[DebateMessage] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    financial_data: dict = field(default_factory=dict)   # ROI, break-even, etc.
    total_rounds: int = 0
    timestamp: str = ""


# ---------------------------------------------------------------------------
#  War Room — The Consensus Engine
# ---------------------------------------------------------------------------

class WarRoom:
    """
    The War Room orchestrates 4 agents through a structured debate process
    to evaluate a business idea and reach consensus.

    Flow:
        gather_intel() → run_debate() → evaluate_consensus() → build_report()
                ↑                                    |
                └────── (if NEEDS_REVISION) ─────────┘
    """

    MAX_DEBATE_ROUNDS = 5       # Prevent infinite loops
    MAX_REVISION_CYCLES = 3     # Max times the idea can loop back
    CONSENSUS_THRESHOLD = 0.6   # 60% agreement needed for consensus

    def __init__(self, llm_provider=None):
        """
        Initialize the War Room.

        Args:
            llm_provider: The LLM connection (OpenRouter API wrapper).
                          Will be built in models/llm_provider.py
        """
        self.llm = llm_provider
        self.agents = {}            # Will hold the 4 agent instances
        self.debate_history: list[DebateMessage] = []
        self.revision_count = 0

    # ------------------------------------------------------------------
    #  Agent Registration
    # ------------------------------------------------------------------

    def register_agent(self, name: str, agent) -> None:
        """
        Register an agent in the War Room.

        Args:
            name: Agent identifier (strategist, researcher, quant, executioner)
            agent: Agent instance (from agents/ directory)
        """
        self.agents[name] = agent
        print(f"  ⚔️  Agent [{name.upper()}] entered the War Room.")

    # ------------------------------------------------------------------
    #  Phase 1: Intelligence Gathering (Independent Analysis)
    # ------------------------------------------------------------------

    def gather_intel(self, idea: dict) -> list[AgentAnalysis]:
        """
        Each agent independently analyzes the business idea.
        No communication between agents at this stage.

        Args:
            idea: Dict with keys like 'description', 'budget',
                  'target_market', 'revenue_model', etc.

        Returns:
            List of AgentAnalysis objects, one per agent.
        """
        print("\n" + "=" * 60)
        print("  📡 PHASE 1: INTELLIGENCE GATHERING")
        print("=" * 60)

        analyses = []

        # -- Strategist: Build the business model --
        if "strategist" in self.agents:
            print("\n  🧠 Strategist is building the business model...")
            strategist_result = self.agents["strategist"].analyze(idea)
            analyses.append(strategist_result)

        # -- Researcher: Find competitors & market facts --
        if "researcher" in self.agents:
            print("  🔍 Researcher is hunting for market intelligence...")
            researcher_result = self.agents["researcher"].analyze(idea)
            analyses.append(researcher_result)

        # -- Quant: Run Monte Carlo & financial models --
        if "quant" in self.agents:
            print("  📊 Quant is running Monte Carlo simulation (1000 scenarios)...")
            quant_result = self.agents["quant"].analyze(idea)
            analyses.append(quant_result)

        # -- Executioner: Find reasons it will fail --
        if "executioner" in self.agents:
            print("  ⚔️  Executioner is looking for kill shots...")
            executioner_result = self.agents["executioner"].analyze(
                idea, prior_analyses=analyses  # Executioner sees others' work
            )
            analyses.append(executioner_result)

        return analyses

    # ------------------------------------------------------------------
    #  Phase 2: The Debate (Structured Argumentation)
    # ------------------------------------------------------------------

    def run_debate(self, analyses: list[AgentAnalysis], idea: dict) -> list[DebateMessage]:
        """
        Structured debate between agents.

        Round structure:
            1. Executioner challenges the weakest claims
            2. Challenged agent defends
            3. Other agents weigh in (agree/rebut)
            4. Scores may be updated

        Args:
            analyses: Results from gather_intel()
            idea: The original business idea

        Returns:
            Full debate transcript as list of DebateMessages
        """
        print("\n" + "=" * 60)
        print("  💬 PHASE 2: THE DEBATE")
        print("=" * 60)

        debate_log = []

        for round_num in range(1, self.MAX_DEBATE_ROUNDS + 1):
            print(f"\n  ──── Round {round_num}/{self.MAX_DEBATE_ROUNDS} ────")

            # Step 1: Executioner opens with a challenge
            challenge = self._executioner_challenge(analyses, round_num)
            if challenge:
                debate_log.append(challenge)
                print(f"  ⚔️  Executioner: {challenge.content[:80]}...")

                # Step 2: Target agent defends
                defense = self._agent_defend(
                    challenge.target, challenge, analyses, round_num
                )
                if defense:
                    debate_log.append(defense)
                    print(f"  🛡️  {defense.sender}: {defense.content[:80]}...")

                # Step 3: Other agents weigh in
                for agent_name in self.agents:
                    if agent_name not in [challenge.sender, challenge.target]:
                        opinion = self._agent_weigh_in(
                            agent_name, challenge, defense, analyses, round_num
                        )
                        if opinion:
                            debate_log.append(opinion)
                            print(f"  💭  {opinion.sender}: {opinion.content[:80]}...")

            # Step 4: Check if early consensus is possible
            if self._check_early_consensus(analyses):
                print(f"\n  ✅ Early consensus reached at round {round_num}!")
                break

        self.debate_history.extend(debate_log)
        return debate_log

    # ------------------------------------------------------------------
    #  Phase 3: Consensus Evaluation
    # ------------------------------------------------------------------

    def evaluate_consensus(self, analyses: list[AgentAnalysis]) -> Verdict:
        """
        Determine the final verdict based on all agent scores and debate.

        Rules:
            - If Executioner score < 3.0 AND others can't refute → REJECTED
            - If average score >= 7.0 → APPROVED
            - If Executioner found fixable issues → NEEDS_REVISION
            - Otherwise → NO_CONSENSUS

        Args:
            analyses: Updated analyses after the debate

        Returns:
            A Verdict enum value
        """
        print("\n" + "=" * 60)
        print("  ⚖️  PHASE 3: CONSENSUS EVALUATION")
        print("=" * 60)

        scores = {a.agent_name: a.score for a in analyses}
        avg_score = sum(scores.values()) / len(scores) if scores else 0

        executioner_score = scores.get("executioner", 5.0)

        print(f"\n  Agent Scores: {json.dumps(scores, indent=2)}")
        print(f"  Average Score: {avg_score:.1f}/10")
        print(f"  Executioner Score: {executioner_score:.1f}/10")

        # ---- Decision Logic ----

        # Case 1: Executioner killed it and it's truly dead
        if executioner_score < 3.0 and avg_score < 5.0:
            verdict = Verdict.REJECTED
            print("\n  ❌ VERDICT: REJECTED — Fatal flaws identified.")

        # Case 2: Strong approval across the board
        elif avg_score >= 7.0 and executioner_score >= 5.0:
            verdict = Verdict.APPROVED
            print("\n  ✅ VERDICT: APPROVED — Idea is viable!")

        # Case 3: Fixable issues exist
        elif executioner_score < 5.0 and avg_score >= 5.0:
            if self.revision_count < self.MAX_REVISION_CYCLES:
                verdict = Verdict.NEEDS_REVISION
                self.revision_count += 1
                print(f"\n  🔄 VERDICT: NEEDS REVISION (cycle {self.revision_count}/{self.MAX_REVISION_CYCLES})")
            else:
                # Too many revisions — force a decision
                verdict = Verdict.NO_CONSENSUS
                print("\n  ⚠️  VERDICT: NO CONSENSUS — Max revisions reached.")

        # Case 4: Moderate approval
        elif avg_score >= 5.0:
            verdict = Verdict.APPROVED
            print("\n  ✅ VERDICT: APPROVED (with reservations)")

        # Case 5: No agreement
        else:
            verdict = Verdict.NO_CONSENSUS
            print("\n  ⚠️  VERDICT: NO CONSENSUS")

        return verdict

    # ------------------------------------------------------------------
    #  Phase 4: Report Generation
    # ------------------------------------------------------------------

    def build_report(
        self,
        idea: dict,
        verdict: Verdict,
        analyses: list[AgentAnalysis],
        debate_log: list[DebateMessage]
    ) -> WarRoomReport:
        """
        Compile everything into a final deliverable for the user.

        Args:
            idea: Original business idea
            verdict: The consensus verdict
            analyses: All agent analyses
            debate_log: Full debate transcript

        Returns:
            WarRoomReport with all data
        """
        print("\n" + "=" * 60)
        print("  📄 PHASE 4: BUILDING FINAL REPORT")
        print("=" * 60)

        scores = [a.score for a in analyses]
        final_score = sum(scores) / len(scores) if scores else 0.0

        # Extract Monte Carlo probability from Quant's data
        quant_data = next(
            (a.raw_data for a in analyses if a.agent_name == "quant"), {}
        )
        success_probability = quant_data.get("success_probability", 0.0)

        # Aggregate all risks
        all_risks = []
        for a in analyses:
            all_risks.extend(a.key_risks)

        # Aggregate all strengths
        all_strengths = []
        for a in analyses:
            all_strengths.extend(a.key_strengths)

        # Build recommendations based on verdict
        recommendations = self._generate_recommendations(verdict, analyses)

        report = WarRoomReport(
            idea_summary=idea.get("description", "No description provided"),
            verdict=verdict,
            final_score=round(final_score, 1),
            success_probability=round(success_probability, 4),
            risk_analysis={
                "critical_risks": all_risks,
                "strengths": all_strengths,
                "risk_score": round(10.0 - final_score, 1),
            },
            agent_analyses=analyses,
            debate_log=debate_log,
            recommendations=recommendations,
            financial_data=quant_data,
            total_rounds=len(set(m.round_number for m in debate_log)),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        )

        self._print_report(report)
        return report

    # ------------------------------------------------------------------
    #  Main Execution — The Full Pipeline
    # ------------------------------------------------------------------

    def execute(self, idea: dict) -> WarRoomReport:
        """
        Run the complete War Room analysis pipeline.

        This is the main entry point. It loops through:
            gather_intel → debate → evaluate → (revise?) → report

        Args:
            idea: Business idea dict with keys:
                - description (str): What the business does
                - budget (float): Available capital
                - target_market (str): Who the customers are
                - revenue_model (str): How it makes money
                - competitors (list[str]): Known competitors

        Returns:
            WarRoomReport — the final deliverable
        """
        print("\n" + "🔥" * 30)
        print("  THE IRON LEDGER — WAR ROOM ACTIVATED")
        print("🔥" * 30)
        print(f"\n  📌 Idea: {idea.get('description', 'N/A')}")
        print(f"  💰 Budget: ${idea.get('budget', 'N/A'):,}")
        print(f"  🎯 Market: {idea.get('target_market', 'N/A')}")

        while True:
            # Phase 1: Each agent analyzes independently
            analyses = self.gather_intel(idea)

            # Phase 2: Structured debate
            debate_log = self.run_debate(analyses, idea)

            # Phase 3: Evaluate consensus
            verdict = self.evaluate_consensus(analyses)

            # If needs revision and we haven't exceeded max cycles, loop back
            if verdict == Verdict.NEEDS_REVISION:
                print("\n  🔄 Looping back — Executioner found fixable issues...")
                # Update the idea context with feedback for the next round
                idea["_revision_feedback"] = self._extract_revision_notes(analyses)
                continue

            # Otherwise, we have a final answer
            break

        # Phase 4: Build and return the report
        report = self.build_report(idea, verdict, analyses, debate_log)
        return report

    # ------------------------------------------------------------------
    #  Private Helper Methods
    # ------------------------------------------------------------------

    def _executioner_challenge(
        self, analyses: list[AgentAnalysis], round_num: int
    ) -> Optional[DebateMessage]:
        """
        The Executioner picks the weakest claim and challenges it.
        Uses the LLM to generate a targeted, brutal critique.
        """
        if "executioner" not in self.agents:
            return None

        # Find the agent with the highest score (most optimistic = most vulnerable)
        target = max(
            [a for a in analyses if a.agent_name != "executioner"],
            key=lambda a: a.score,
            default=None,
        )
        if not target:
            return None

        # Ask the Executioner agent to generate a challenge
        challenge_context = {
            "target_agent": target.agent_name,
            "target_analysis": target.analysis,
            "target_score": target.score,
            "target_strengths": target.key_strengths,
            "debate_history": [
                {"sender": m.sender, "content": m.content}
                for m in self.debate_history[-10:]  # Last 10 messages for context
            ],
        }

        challenge_text = self.agents["executioner"].challenge(challenge_context)

        return DebateMessage(
            sender="executioner",
            target=target.agent_name,
            content=challenge_text,
            message_type="challenge",
            round_number=round_num,
        )

    def _agent_defend(
        self,
        agent_name: str,
        challenge: DebateMessage,
        analyses: list[AgentAnalysis],
        round_num: int,
    ) -> Optional[DebateMessage]:
        """The challenged agent defends their position."""
        if agent_name not in self.agents:
            return None

        defense_context = {
            "challenge": challenge.content,
            "my_analysis": next(
                (a.analysis for a in analyses if a.agent_name == agent_name), ""
            ),
        }

        defense_text = self.agents[agent_name].defend(defense_context)

        return DebateMessage(
            sender=agent_name,
            target="executioner",
            content=defense_text,
            message_type="defense",
            round_number=round_num,
        )

    def _agent_weigh_in(
        self,
        agent_name: str,
        challenge: DebateMessage,
        defense: Optional[DebateMessage],
        analyses: list[AgentAnalysis],
        round_num: int,
    ) -> Optional[DebateMessage]:
        """An agent gives their opinion on the ongoing debate."""
        if agent_name not in self.agents:
            return None

        context = {
            "challenge": challenge.content,
            "defense": defense.content if defense else "",
            "challenger": challenge.sender,
            "defender": challenge.target,
        }

        opinion_text = self.agents[agent_name].weigh_in(context)

        return DebateMessage(
            sender=agent_name,
            target="all",
            content=opinion_text,
            message_type="agreement" if "agree" in opinion_text.lower() else "rebuttal",
            round_number=round_num,
        )

    def _check_early_consensus(self, analyses: list[AgentAnalysis]) -> bool:
        """
        Check if agents have converged enough for early termination.
        If the standard deviation of scores is below a threshold, we're done.
        """
        scores = [a.score for a in analyses]
        if not scores:
            return False

        avg = sum(scores) / len(scores)
        variance = sum((s - avg) ** 2 for s in scores) / len(scores)
        std_dev = variance ** 0.5

        # If all agents are within ~1.5 points of each other, consensus is reached
        return std_dev < 1.5

    def _extract_revision_notes(self, analyses: list[AgentAnalysis]) -> list[str]:
        """Extract the Executioner's key criticisms for the revision loop."""
        executioner = next(
            (a for a in analyses if a.agent_name == "executioner"), None
        )
        if executioner:
            return executioner.key_risks
        return []

    def _generate_recommendations(
        self, verdict: Verdict, analyses: list[AgentAnalysis]
    ) -> list[str]:
        """Generate actionable recommendations based on the verdict."""
        recommendations = []

        if verdict == Verdict.APPROVED:
            recommendations.append("✅ Proceed with the business plan.")
            # Get strategist's key strengths as action items
            strategist = next(
                (a for a in analyses if a.agent_name == "strategist"), None
            )
            if strategist:
                for strength in strategist.key_strengths[:3]:
                    recommendations.append(f"  → Leverage: {strength}")

        elif verdict == Verdict.REJECTED:
            recommendations.append("❌ Do NOT proceed with this idea.")
            executioner = next(
                (a for a in analyses if a.agent_name == "executioner"), None
            )
            if executioner:
                for risk in executioner.key_risks[:3]:
                    recommendations.append(f"  → Fatal flaw: {risk}")

        elif verdict == Verdict.NO_CONSENSUS:
            recommendations.append("⚠️  Agents could not reach consensus.")
            recommendations.append("  → Consider refining the idea and re-submitting.")
            recommendations.append("  → Focus on addressing the top risks identified.")

        return recommendations

    def _print_report(self, report: WarRoomReport) -> None:
        """Pretty-print the final report to the console."""
        print("\n" + "=" * 60)
        print("  📊 THE IRON LEDGER — FINAL REPORT")
        print("=" * 60)

        # Verdict banner
        verdict_icons = {
            Verdict.APPROVED: "✅ APPROVED",
            Verdict.REJECTED: "❌ REJECTED",
            Verdict.NEEDS_REVISION: "🔄 NEEDS REVISION",
            Verdict.NO_CONSENSUS: "⚠️  NO CONSENSUS",
        }
        print(f"\n  Verdict:              {verdict_icons[report.verdict]}")
        print(f"  Final Score:          {report.final_score}/10")
        print(f"  Success Probability:  {report.success_probability * 100:.1f}%")
        print(f"  Debate Rounds:        {report.total_rounds}")
        print(f"  Timestamp:            {report.timestamp}")

        # Risk summary
        print(f"\n  ── Risk Analysis ──")
        for risk in report.risk_analysis.get("critical_risks", [])[:5]:
            print(f"  🔴 {risk}")

        # Strengths
        print(f"\n  ── Strengths ──")
        for strength in report.risk_analysis.get("strengths", [])[:5]:
            print(f"  🟢 {strength}")

        # Recommendations
        print(f"\n  ── Recommendations ──")
        for rec in report.recommendations:
            print(f"  {rec}")

        # Financial data
        if report.financial_data:
            print(f"\n  ── Financial Summary ──")
            for key, val in report.financial_data.items():
                if key != "simulation_results":  # Skip raw arrays
                    print(f"  💰 {key}: {val}")

        print("\n" + "=" * 60)


# ---------------------------------------------------------------------------
#  Standalone test (will be replaced by main.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("🧠 brain.py loaded successfully.")
    print("   Waiting for agents to be registered...")
    print("   Run main.py to start the War Room.\n")

    # Quick sanity check — data models work
    test_analysis = AgentAnalysis(
        agent_name="test",
        role="tester",
        analysis="This is a test.",
        score=7.5,
        key_risks=["Test risk"],
        key_strengths=["Test strength"],
    )
    print(f"   ✅ AgentAnalysis created: {test_analysis.agent_name} — score {test_analysis.score}")

    room = WarRoom()
    print(f"   ✅ WarRoom initialized — max rounds: {room.MAX_DEBATE_ROUNDS}")
    print(f"   ✅ Revision limit: {room.MAX_REVISION_CYCLES}")
    print("\n   All systems nominal. Ready for deployment. 🚀")
