"""
🔥 main.py — The Iron Ledger: War Room Entry Point
=====================================================
This is the main entry point for the business idea analysis system.
It connects all 4 agents, runs the sequential pipeline, and presents
the final verdict with a rich terminal UI.

Usage:
    python main.py
"""

import sys
import time
import traceback

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Prompt
from rich.rule import Rule
from rich.align import Align
from rich.live import Live
from rich.spinner import Spinner
from rich.markdown import Markdown
from rich import box

from models.llm_provider import LLMProvider
from agents.strategist import Strategist
from agents.researcher import Researcher
from agents.quant import Quant
from agents.executioner import Executioner
from brain import WarRoom, Verdict

# ---------------------------------------------------------------------------
#  Console Setup
# ---------------------------------------------------------------------------
console = Console()


# ---------------------------------------------------------------------------
#  The War Room Banner
# ---------------------------------------------------------------------------

BANNER = r"""
[bold red]
  ████████╗██╗  ██╗███████╗    ██╗██████╗  ██████╗ ███╗   ██╗
  ╚══██╔══╝██║  ██║██╔════╝    ██║██╔══██╗██╔═══██╗████╗  ██║
     ██║   ███████║█████╗      ██║██████╔╝██║   ██║██╔██╗ ██║
     ██║   ██╔══██║██╔══╝      ██║██╔══██╗██║   ██║██║╚██╗██║
     ██║   ██║  ██║███████╗    ██║██║  ██║╚██████╔╝██║ ╚████║
     ╚═╝   ╚═╝  ╚═╝╚══════╝    ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
[/bold red]
[bold white]
                  ██╗     ███████╗██████╗  ██████╗ ███████╗██████╗
                  ██║     ██╔════╝██╔══██╗██╔════╝ ██╔════╝██╔══██╗
                  ██║     █████╗  ██║  ██║██║  ███╗█████╗  ██████╔╝
                  ██║     ██╔══╝  ██║  ██║██║   ██║██╔══╝  ██╔══██╗
                  ███████╗███████╗██████╔╝╚██████╔╝███████╗██║  ██║
                  ╚══════╝╚══════╝╚═════╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝
[/bold white]
"""

WELCOME_MESSAGE = """
[bold yellow]⚠️  WARNING: You are about to enter THE WAR ROOM.[/bold yellow]

[dim]Your idea will be interrogated by 4 ruthless AI agents.
They will dissect it, stress-test it, and try to DESTROY it.
Only the strongest ideas survive.[/dim]

[bold red]🧠 The Visionary[/bold red]   — Will forge your idea into a battle plan
[bold blue]🔍 The Spy[/bold blue]         — Will uncover every enemy on the battlefield  
[bold cyan]📊 The Quant[/bold cyan]       — Will run 1,000 war simulations on your numbers
[bold red]⚔️  The Executioner[/bold red]  — Will try to KILL your idea. No mercy.
"""


# ---------------------------------------------------------------------------
#  Helper: Status Animation for Each Agent
# ---------------------------------------------------------------------------

def run_agent_with_status(agent_name: str, icon: str, color: str, task_fn):
    """
    Run an agent's task with a live spinner animation.

    Args:
        agent_name: Display name of the agent
        icon: Emoji icon
        color: Rich color name
        task_fn: Function to execute (returns AgentAnalysis)

    Returns:
        The result of task_fn()
    """
    result = None
    error = None

    with console.status(
        f"[bold {color}]{icon} {agent_name} is working...[/bold {color}]",
        spinner="dots",
        spinner_style=color,
    ):
        try:
            result = task_fn()
        except Exception as e:
            error = e

    if error:
        console.print(
            f"  [bold red]❌ {agent_name} FAILED: {type(error).__name__}: {error}[/bold red]"
        )
        raise error

    console.print(f"  [bold {color}]✅ {agent_name} — DONE[/bold {color}]")
    return result


# ---------------------------------------------------------------------------
#  Helper: Display Agent Analysis Result
# ---------------------------------------------------------------------------

def display_analysis(analysis, color: str, icon: str):
    """Show a summary panel for one agent's analysis."""
    # Build a summary table
    table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    table.add_column("Key", style="bold white", width=20)
    table.add_column("Value", style="white")

    table.add_row("Score", f"[bold]{analysis.score}/10[/bold]")

    if analysis.key_risks:
        risks_text = "\n".join(f"  🔴 {r[:80]}" for r in analysis.key_risks[:3])
        table.add_row("Risks", risks_text)

    if analysis.key_strengths:
        strengths_text = "\n".join(f"  🟢 {s[:80]}" for s in analysis.key_strengths[:3])
        table.add_row("Strengths", strengths_text)

    panel = Panel(
        table,
        title=f"{icon} {analysis.role}",
        title_align="left",
        border_style=color,
        padding=(1, 2),
    )
    console.print(panel)


# ---------------------------------------------------------------------------
#  Helper: Display Final Verdict
# ---------------------------------------------------------------------------

def display_verdict(report):
    """Show the final War Room verdict in a dramatic colored box."""
    verdict = report.verdict
    score = report.final_score
    prob = report.success_probability

    # Determine color and message based on verdict
    if verdict == Verdict.APPROVED:
        border_color = "green"
        verdict_icon = "✅"
        verdict_text = "IDEA APPROVED"
        subtitle = "The War Room has spoken. Your idea SURVIVES."
    elif verdict == Verdict.REJECTED:
        border_color = "red"
        verdict_icon = "💀"
        verdict_text = "IDEA REJECTED"
        subtitle = "The War Room has spoken. Your idea is DEAD."
    elif verdict == Verdict.NEEDS_REVISION:
        border_color = "yellow"
        verdict_icon = "🔄"
        verdict_text = "NEEDS REVISION"
        subtitle = "Fixable flaws detected. Revise and re-submit."
    else:
        border_color = "yellow"
        verdict_icon = "⚠️"
        verdict_text = "NO CONSENSUS"
        subtitle = "The agents could not agree. Proceed with caution."

    # --- Build the verdict content ---
    content = Text()
    content.append(f"\n  {verdict_icon}  ", style=f"bold {border_color}")
    content.append(verdict_text, style=f"bold {border_color} underline")
    content.append(f"\n  {subtitle}\n\n", style=f"dim {border_color}")

    # Score bar
    score_bar = "█" * int(score) + "░" * (10 - int(score))
    content.append(f"  Final Score:          ", style="bold white")
    score_color = "green" if score >= 7 else "yellow" if score >= 5 else "red"
    content.append(f"{score:.1f}/10 [{score_bar}]\n", style=f"bold {score_color}")

    # Success probability
    prob_pct = prob * 100
    content.append(f"  Success Probability:  ", style="bold white")
    prob_color = "green" if prob_pct >= 70 else "yellow" if prob_pct >= 40 else "red"
    content.append(f"{prob_pct:.1f}%\n", style=f"bold {prob_color}")

    # Debate rounds
    content.append(f"  Debate Rounds:        ", style="bold white")
    content.append(f"{report.total_rounds}\n", style="bold white")

    # Recommendations
    if report.recommendations:
        content.append(f"\n  ── Recommendations ──\n", style="bold white")
        for rec in report.recommendations:
            content.append(f"  {rec}\n", style="white")

    # Risk summary
    risks = report.risk_analysis.get("critical_risks", [])
    if risks:
        content.append(f"\n  ── Critical Risks ──\n", style="bold red")
        for risk in risks[:5]:
            content.append(f"  🔴 {risk[:90]}\n", style="red")

    # Strengths summary
    strengths = report.risk_analysis.get("strengths", [])
    if strengths:
        content.append(f"\n  ── Key Strengths ──\n", style="bold green")
        for s in strengths[:5]:
            content.append(f"  🟢 {s[:90]}\n", style="green")

    content.append("\n")

    # Financial highlights
    fin = report.financial_data
    if fin:
        content.append(f"  ── Financial Summary ──\n", style="bold cyan")
        if "roi" in fin:
            content.append(f"  ROI:               {fin['roi']:.1f}%\n", style="cyan")
        if "mean_profit" in fin:
            content.append(f"  Mean Profit:       ${fin['mean_profit']:,.0f}\n", style="cyan")
        if "worst_case" in fin:
            content.append(f"  Worst Case (5%):   ${fin['worst_case']:,.0f}\n", style="cyan")
        if "best_case" in fin:
            content.append(f"  Best Case (95%):   ${fin['best_case']:,.0f}\n", style="cyan")
        if "break_even_months" in fin:
            content.append(
                f"  Break-Even:        {fin['break_even_months']} months\n",
                style="cyan",
            )
        content.append("\n")

    panel = Panel(
        content,
        title="[bold white]⚔️  THE IRON LEDGER — FINAL VERDICT  ⚔️[/bold white]",
        title_align="center",
        subtitle=f"[dim]Generated at {report.timestamp}[/dim]",
        subtitle_align="center",
        border_style=f"bold {border_color}",
        padding=(1, 3),
        width=80,
    )

    console.print()
    console.print(Align.center(panel))
    console.print()


# ---------------------------------------------------------------------------
#  Helper: Collect User Input
# ---------------------------------------------------------------------------

def collect_idea() -> dict:
    """Interview the user to collect their business idea details."""
    console.print(Rule("[bold white]📋 IDEA INTAKE FORM[/bold white]", style="red"))
    console.print()

    # Business idea description
    description = Prompt.ask(
        "[bold yellow]💡 Describe your business idea[/bold yellow]\n"
        "[dim]   (Be as detailed as possible)[/dim]"
    )

    # Budget
    while True:
        budget_str = Prompt.ask(
            "\n[bold yellow]💰 Initial budget (USD)[/bold yellow]",
            default="50000",
        )
        try:
            budget = float(budget_str.replace(",", "").replace("$", ""))
            break
        except ValueError:
            console.print("[red]  Invalid number. Try again.[/red]")

    # Target market / country
    target_market = Prompt.ask(
        "\n[bold yellow]🌍 Target market / country[/bold yellow]",
        default="Global",
    )

    # Revenue model (optional)
    revenue_model = Prompt.ask(
        "\n[bold yellow]💳 Revenue model[/bold yellow]\n"
        "[dim]   (subscription, per-unit, commission, ads, etc.)[/dim]",
        default="Not specified",
    )

    # Known competitors (optional)
    competitors_str = Prompt.ask(
        "\n[bold yellow]🏢 Known competitors[/bold yellow]\n"
        "[dim]   (comma-separated, or 'none')[/dim]",
        default="none",
    )
    competitors = []
    if competitors_str.lower() != "none":
        competitors = [c.strip() for c in competitors_str.split(",") if c.strip()]

    idea = {
        "description": description,
        "budget": budget,
        "target_market": target_market,
        "revenue_model": revenue_model,
        "competitors": competitors,
    }

    # Show summary
    console.print()
    summary_table = Table(
        title="📌 Idea Summary", box=box.ROUNDED, border_style="yellow"
    )
    summary_table.add_column("Field", style="bold white", width=18)
    summary_table.add_column("Value", style="white")
    summary_table.add_row("Idea", description[:60] + ("..." if len(description) > 60 else ""))
    summary_table.add_row("Budget", f"${budget:,.0f}")
    summary_table.add_row("Market", target_market)
    summary_table.add_row("Revenue Model", revenue_model)
    summary_table.add_row("Competitors", ", ".join(competitors) if competitors else "None listed")
    console.print(summary_table)
    console.print()

    return idea


# ---------------------------------------------------------------------------
#  Main Pipeline
# ---------------------------------------------------------------------------

def run_war_room():
    """
    The main execution pipeline:
        1. Show welcome banner
        2. Collect user's idea
        3. Run 4 agents sequentially with live status
        4. Run debate
        5. Display final verdict
    """

    # ── Step 0: Welcome Banner ──
    console.print(BANNER)
    welcome_panel = Panel(
        WELCOME_MESSAGE,
        title="[bold red]⚔️  THE WAR ROOM  ⚔️[/bold red]",
        title_align="center",
        border_style="bold red",
        padding=(1, 4),
    )
    console.print(Align.center(welcome_panel))
    console.print()

    # ── Step 1: Collect the idea ──
    idea = collect_idea()

    # Confirm before entering the war room
    proceed = Prompt.ask(
        "[bold red]⚠️  Ready to enter THE WAR ROOM?[/bold red]",
        choices=["y", "n"],
        default="y",
    )
    if proceed.lower() != "y":
        console.print("\n[dim]Retreat is wisdom... sometimes.[/dim]\n")
        return

    console.print()
    console.print(Rule("[bold red]⚔️  ENTERING THE WAR ROOM  ⚔️[/bold red]", style="red"))
    console.print()
    time.sleep(1)

    # ── Step 2: Initialize the system ──
    try:
        with console.status(
            "[bold white]🔌 Initializing AI systems...[/bold white]",
            spinner="dots",
        ):
            llm = LLMProvider()
            war_room = WarRoom(llm_provider=llm)

            strategist = Strategist(llm)
            researcher = Researcher(llm)
            quant = Quant(llm)
            executioner = Executioner(llm)

            war_room.register_agent("strategist", strategist)
            war_room.register_agent("researcher", researcher)
            war_room.register_agent("quant", quant)
            war_room.register_agent("executioner", executioner)

        console.print("[bold green]  ✅ All systems online.[/bold green]\n")
        time.sleep(0.5)

    except Exception as e:
        console.print(f"\n[bold red]💥 SYSTEM FAILURE: {e}[/bold red]")
        console.print("[dim]Check your .env file and API key.[/dim]")
        return

    # ── Step 3: The Pipeline — Run each agent sequentially ──

    analyses = []

    console.print(Rule("[bold white]📡 PHASE 1: INTELLIGENCE GATHERING (Parallel Execution)[/bold white]", style="blue"))
    console.print()

    # Import concurrent.futures at the top level or locally
    import concurrent.futures

    def run_strat():
        return strategist.analyze(idea)
    def run_res():
        return researcher.analyze(idea)
    def run_quant():
        return quant.analyze(idea)

    with console.status("[bold blue]📡 Visionary, Spy, and Quant are analyzing the idea simultaneously...[/bold blue]", spinner="dots"):
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # Start all three agents at the same time
            future_strat = executor.submit(run_strat)
            future_res = executor.submit(run_res)
            future_quant = executor.submit(run_quant)

            # Wait and display results as they finish
            try:
                strat_res = future_strat.result()
                analyses.append(strat_res)
                display_analysis(strat_res, "red", "🧠")
                console.print("  [bold red]✅ THE VISIONARY — DONE[/bold red]\n")
            except Exception as e:
                console.print(f"[bold red]  ⚠️  Strategist failed: {e}[/bold red]\n")

            try:
                res_res = future_res.result()
                analyses.append(res_res)
                display_analysis(res_res, "blue", "🔍")
                console.print("  [bold blue]✅ THE SPY — DONE[/bold blue]\n")
            except Exception as e:
                console.print(f"[bold red]  ⚠️  Researcher failed: {e}[/bold red]\n")

            try:
                quant_res = future_quant.result()
                analyses.append(quant_res)
                display_analysis(quant_res, "cyan", "📊")
                console.print("  [bold cyan]✅ THE QUANT — DONE[/bold cyan]\n")
            except Exception as e:
                console.print(f"[bold red]  ⚠️  Quant failed: {e}[/bold red]\n")

    # --- Agent 4: The Executioner ---
    console.print()
    console.print(Rule(
        "[bold red]⚔️  THE EXECUTIONER ENTERS[/bold red]",
        style="bold red",
    ))
    console.print("[dim]  All prior analyses are being handed to the Executioner...[/dim]\n")
    time.sleep(0.5)

    try:
        executioner_result = run_agent_with_status(
            agent_name="THE EXECUTIONER — Writing Death-or-Survival Verdict",
            icon="⚔️",
            color="red",
            task_fn=lambda: executioner.analyze(idea, prior_analyses=analyses),
        )
        analyses.append(executioner_result)
        display_analysis(executioner_result, "red", "⚔️")
    except Exception as e:
        console.print(f"[bold red]  ⚠️  Executioner failed: {e}[/bold red]")
        console.print("[dim]  Generating report with available data...[/dim]\n")

    # ── Step 4: The Debate ──
    if len(analyses) >= 3:
        console.print()
        console.print(Rule(
            "[bold white]💬 PHASE 2: THE DEBATE[/bold white]",
            style="yellow",
        ))
        console.print("[dim]  Agents are arguing with each other...[/dim]\n")

        try:
            with console.status(
                "[bold yellow]💬 Debate in progress — agents are fighting...[/bold yellow]",
                spinner="dots",
                spinner_style="yellow",
            ):
                debate_log = war_room.run_debate(analyses, idea)

            console.print(
                f"  [bold yellow]✅ Debate concluded — "
                f"{len(debate_log)} messages exchanged.[/bold yellow]\n"
            )

            # Show a few key debate moments
            if debate_log:
                debate_table = Table(
                    title="💬 Key Debate Moments",
                    box=box.SIMPLE_HEAVY,
                    border_style="yellow",
                    show_lines=True,
                )
                debate_table.add_column("Agent", style="bold", width=15)
                debate_table.add_column("Type", style="dim", width=12)
                debate_table.add_column("Message", width=50)

                for msg in debate_log[:6]:  # Show max 6 messages
                    type_color = {
                        "challenge": "red",
                        "defense": "green",
                        "agreement": "cyan",
                        "rebuttal": "yellow",
                    }.get(msg.message_type, "white")

                    debate_table.add_row(
                        msg.sender.upper(),
                        f"[{type_color}]{msg.message_type}[/{type_color}]",
                        msg.content[:100] + ("..." if len(msg.content) > 100 else ""),
                    )
                console.print(debate_table)
                console.print()

        except Exception as e:
            console.print(f"  [bold yellow]⚠️  Debate phase failed: {e}[/bold yellow]")
            console.print("[dim]  Proceeding to verdict with available data...[/dim]\n")
            debate_log = []
    else:
        debate_log = []
        console.print("\n[dim]  Not enough agents succeeded for a debate.[/dim]\n")

    # ── Step 5: Consensus & Final Verdict ──
    console.print(Rule(
        "[bold white]⚖️  PHASE 3: FINAL JUDGMENT[/bold white]",
        style="red",
    ))

    try:
        with console.status(
            "[bold white]⚖️  The War Room is deliberating...[/bold white]",
            spinner="dots",
        ):
            verdict = war_room.evaluate_consensus(analyses)
            report = war_room.build_report(idea, verdict, analyses, debate_log)

        # --- THE BIG REVEAL ---
        console.print()
        time.sleep(1)
        display_verdict(report)

        # ── Revision Loop ──
        if verdict == Verdict.NEEDS_REVISION:
            console.print(
                "[bold yellow]🔄 The Executioner found fixable flaws. "
                "Running a revision cycle...[/bold yellow]\n"
            )
            time.sleep(1)

            idea["_revision_feedback"] = war_room._extract_revision_notes(analyses)

            # Re-run strategist and quant with feedback
            try:
                revised_analyses = []

                revised_strat = run_agent_with_status(
                    agent_name="THE VISIONARY — Revising Business Model",
                    icon="🧠",
                    color="yellow",
                    task_fn=lambda: strategist.analyze(idea),
                )
                revised_analyses.append(revised_strat)

                revised_quant = run_agent_with_status(
                    agent_name="THE QUANT — Re-running Simulations",
                    icon="📊",
                    color="yellow",
                    task_fn=lambda: quant.analyze(idea),
                )
                revised_analyses.append(revised_quant)

                # Executioner reviews revisions
                revised_exec = run_agent_with_status(
                    agent_name="THE EXECUTIONER — Re-evaluating",
                    icon="⚔️",
                    color="red",
                    task_fn=lambda: executioner.analyze(idea, prior_analyses=revised_analyses),
                )
                revised_analyses.append(revised_exec)

                # New verdict
                revised_verdict = war_room.evaluate_consensus(revised_analyses)
                revised_report = war_room.build_report(
                    idea, revised_verdict, revised_analyses, debate_log
                )

                console.print()
                console.print(Rule(
                    "[bold white]📋 REVISED VERDICT[/bold white]", style="green"
                ))
                display_verdict(revised_report)

            except Exception as e:
                console.print(
                    f"[bold red]  ⚠️  Revision cycle failed: {e}[/bold red]"
                )

    except Exception as e:
        console.print(f"\n[bold red]💥 JUDGMENT FAILED: {e}[/bold red]")
        console.print(f"[dim]{traceback.format_exc()}[/dim]")

    # ── Farewell ──
    console.print()
    console.print(Rule("[bold white]END OF SESSION[/bold white]", style="red"))
    console.print(
        Align.center(
            "[dim]The Iron Ledger has spoken. "
            "What you do next is your responsibility.[/dim]\n"
        )
    )


# ---------------------------------------------------------------------------
#  Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        run_war_room()
    except KeyboardInterrupt:
        console.print("\n\n[bold red]⚔️  Session terminated by user.[/bold red]\n")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]💥 FATAL ERROR: {e}[/bold red]")
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)
