"""
🔥 main.py — The Iron Ledger: Interactive Terminal Chatbot
=============================================================
This script runs the War Room as an interactive chatbot.
After each agent runs their analysis, the system pauses and allows
the user to chat with that specific agent using memory.
"""

import sys
import time
import traceback

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.prompt import Prompt
from rich.rule import Rule
from rich.align import Align
from rich import box

from models.llm_provider import LLMProvider
from agents.strategist import Strategist
from agents.researcher import Researcher
from agents.quant import Quant
from agents.executioner import Executioner
from brain import WarRoom, Verdict

from prompts.system_prompts import (
    STRATEGIST_PROMPT,
    RESEARCHER_PROMPT,
    QUANT_PROMPT,
    EXECUTIONER_PROMPT
)

# ---------------------------------------------------------------------------
#  Console Setup
# ---------------------------------------------------------------------------
console = Console()

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
[bold yellow]⚠️  شما در حال ورود به حالت چت تعاملی THE WAR ROOM هستید.[/bold yellow]

[dim]در این حالت، پس از اینکه هر مأمور گزارش خود را داد، شما می‌توانید با او گفتگوی زنده داشته باشید.
مأمورها دارای حافظه هستند و می‌توانید از آن‌ها بخواهید گزارش خود را تغییر دهند یا شفاف‌سازی کنند.[/dim]
"""

# ---------------------------------------------------------------------------
#  Helper: Interactive Chat Loop with Memory
# ---------------------------------------------------------------------------

def interactive_agent_chat(agent_id: str, display_name: str, color: str, sys_prompt: str, idea: dict, agent_analysis, llm_provider):
    """
    Creates an interactive while True chat loop for the user to talk with the agent.
    """
    console.print()
    console.print(Rule(f"[bold {color}]💬 جلسه پرسش و پاسخ با {display_name}[/bold {color}]", style=color))
    console.print(f"[dim]شما می‌توانید از {display_name} در مورد تحلیل بالا سوال بپرسید یا با او مخالفت کنید.[/dim]")
    console.print(f"[dim]برای اتمام گفتگو با این مأمور و رفتن به مرحله بعد تایپ کنید: [bold white]next[/bold white] یا [bold white]بعدی[/bold white][/dim]\n")
    
    # Initialize Memory for this specific agent's chat session
    memory = [
        {"role": "system", "content": f"{sys_prompt}\n\nتو باید به زبان فارسی پاسخ دهی. تو در حال یک جلسه بازجویی با صاحب ایده هستی."},
        {"role": "user", "content": f"ایده تجاری من این است:\n{idea}\n\nتحلیل اولیه تو این بود:\n{agent_analysis.analysis}\n\nمن الان قصد دارم در مورد این تحلیل با تو بحث کنم."},
        {"role": "assistant", "content": "تحلیل من در اختیار شماست. چه سوالی دارید یا کجای کار از نظر شما ایراد دارد؟"}
    ]
    
    model_name = llm_provider.models.get(agent_id, "openai/gpt-3.5-turbo")
    
    while True:
        user_msg = Prompt.ask("\n[bold white]شما[/bold white]")
        if user_msg.strip().lower() in ['next', 'بعدی', 'برو مرحله بعد', 'continue', 'skip']:
            console.print(f"\n[bold {color}]--- پایان گفتگو با {display_name} ---[/bold {color}]\n")
            break
            
        memory.append({"role": "user", "content": user_msg})
        
        try:
            with console.status(f"[bold {color}]{display_name} در حال تفکر...[/bold {color}]", spinner="dots"):
                response = llm_provider.client.chat.completions.create(
                    model=model_name,
                    messages=memory,
                    temperature=0.7,
                    max_tokens=1500
                ).choices[0].message.content
                
            memory.append({"role": "assistant", "content": response})
            console.print(f"\n[bold {color}]{display_name}:[/bold {color}]")
            console.print(response)
        except Exception as e:
            console.print(f"[bold red]خطا در ارتباط با {display_name}: {e}[/bold red]")


# ---------------------------------------------------------------------------
#  Helper: Collect User Input
# ---------------------------------------------------------------------------

def collect_idea() -> dict:
    """Interview the user to collect their business idea details."""
    console.print(Rule("[bold white]📋 مصاحبه ورودی ایده[/bold white]", style="red"))
    console.print()

    description = Prompt.ask("[bold yellow]💡 ایده تجاری خود را کامل توضیح دهید[/bold yellow]")
    budget_str = Prompt.ask("\n[bold yellow]💰 بودجه اولیه (به دلار)[/bold yellow]", default="50000")
    try:
        budget = float(budget_str.replace(",", "").replace("$", ""))
    except:
        budget = 50000.0

    target_market = Prompt.ask("\n[bold yellow]🌍 بازار هدف یا کشور[/bold yellow]", default="Global")
    revenue_model = Prompt.ask("\n[bold yellow]💳 مدل درآمدی[/bold yellow]", default="Subscription")
    competitors_str = Prompt.ask("\n[bold yellow]🏢 رقبای اصلی (با کاما جدا کنید)[/bold yellow]", default="none")
    
    competitors = []
    if competitors_str.lower() not in ["none", "هیچکس", "ندارم"]:
        competitors = [c.strip() for c in competitors_str.split(",") if c.strip()]

    return {
        "description": description,
        "budget": budget,
        "target_market": target_market,
        "revenue_model": revenue_model,
        "competitors": competitors,
    }


# ---------------------------------------------------------------------------
#  Main Interactive Pipeline
# ---------------------------------------------------------------------------

def run_interactive_war_room():
    console.print(BANNER)
    welcome_panel = Panel(
        WELCOME_MESSAGE,
        title="[bold red]⚔️  INTERACTIVE WAR ROOM  ⚔️[/bold red]",
        title_align="center",
        border_style="bold red",
        padding=(1, 4),
    )
    console.print(Align.center(welcome_panel))
    console.print()

    idea = collect_idea()
    console.print(Rule("[bold red]⚔️  درهای اتاق جنگ باز شد  ⚔️[/bold red]", style="red"))
    time.sleep(1)

    try:
        with console.status("[bold white]🔌 در حال اتصال به شبکه‌های عصبی...[/bold white]"):
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
    except Exception as e:
        console.print(f"\n[bold red]💥 SYSTEM FAILURE: {e}[/bold red]")
        return

    analyses = []

    # ---------------------------------------------------------
    # AGENT 1: STRATEGIST
    # ---------------------------------------------------------
    console.print(Rule("[bold red]🧠 ورود The Visionary (استراتژیست)[/bold red]", style="red"))
    with console.status("[bold red]The Visionary در حال ساخت بوم کسب و کار...[/bold red]"):
        strat_res = strategist.analyze(idea)
        analyses.append(strat_res)
    
    console.print(Panel(strat_res.analysis, title="[bold red]🧠 گزارش The Visionary[/bold red]", border_style="red"))
    interactive_agent_chat("strategist", "The Visionary 🧠", "red", STRATEGIST_PROMPT, idea, strat_res, llm)


    # ---------------------------------------------------------
    # AGENT 2: RESEARCHER
    # ---------------------------------------------------------
    console.print(Rule("[bold blue]🔍 ورود The Spy (محقق وب)[/bold blue]", style="blue"))
    with console.status("[bold blue]The Spy در حال جستجوی اینترنت و رقبا...[/bold blue]"):
        res_res = researcher.analyze(idea)
        analyses.append(res_res)
        
    console.print(Panel(res_res.analysis, title="[bold blue]🔍 گزارش The Spy[/bold blue]", border_style="blue"))
    interactive_agent_chat("researcher", "The Spy 🔍", "blue", RESEARCHER_PROMPT, idea, res_res, llm)


    # ---------------------------------------------------------
    # AGENT 3: QUANT
    # ---------------------------------------------------------
    console.print(Rule("[bold cyan]📊 ورود The Quant (ریاضی‌دان)[/bold cyan]", style="cyan"))
    with console.status("[bold cyan]The Quant در حال اجرای شبیه‌سازی مونت‌کارلو در پایتون...[/bold cyan]"):
        quant_res = quant.analyze(idea)
        analyses.append(quant_res)
        
    console.print(Panel(quant_res.analysis, title="[bold cyan]📊 گزارش The Quant[/bold cyan]", border_style="cyan"))
    interactive_agent_chat("quant", "The Quant 📊", "cyan", QUANT_PROMPT, idea, quant_res, llm)


    # ---------------------------------------------------------
    # AGENT 4: EXECUTIONER
    # ---------------------------------------------------------
    console.print(Rule("[bold magenta]⚔️ ورود The Executioner (جلاد)[/bold magenta]", style="magenta"))
    with console.status("[bold magenta]جلاد در حال بررسی باگ‌های ایده شماست...[/bold magenta]"):
        exec_res = executioner.analyze(idea, prior_analyses=analyses)
        analyses.append(exec_res)
        
    console.print(Panel(exec_res.analysis, title="[bold magenta]⚔️ کیفرخواست The Executioner[/bold magenta]", border_style="magenta"))
    interactive_agent_chat("executioner", "The Executioner ⚔️", "magenta", EXECUTIONER_PROMPT, idea, exec_res, llm)


    # ---------------------------------------------------------
    # FINAL VERDICT
    # ---------------------------------------------------------
    console.print(Rule("[bold white]⚖️ صدور حکم نهایی[/bold white]", style="white"))
    with console.status("[bold white]در حال محاسبه امتیاز نهایی و شانس موفقیت...[/bold white]"):
        verdict = war_room.evaluate_consensus(analyses)
        report = war_room.build_report(idea, verdict, analyses, [])
        
    v_color = "green" if verdict == Verdict.APPROVED else "red" if verdict == Verdict.REJECTED else "yellow"
    v_text = "APPROVED ✅" if verdict == Verdict.APPROVED else "REJECTED 💀" if verdict == Verdict.REJECTED else "NEEDS REVISION 🔄"
    
    final_panel = Panel(
        f"[bold {v_color}]حکم سیستم: {v_text}[/bold {v_color}]\n\n"
        f"امتیاز نهایی: {report.final_score}/10\n"
        f"احتمال موفقیت مالی: {report.success_probability * 100:.1f}%\n",
        title="[bold white]THE IRON LEDGER VERDICT[/bold white]",
        border_style=v_color,
        padding=(1, 4)
    )
    console.print()
    console.print(Align.center(final_panel))
    console.print("\n[dim]پایان جلسه تعاملی. خسته نباشید.[/dim]\n")


if __name__ == "__main__":
    try:
        run_interactive_war_room()
    except KeyboardInterrupt:
        console.print("\n\n[bold red]⚔️ Session terminated by user.[/bold red]\n")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]💥 FATAL ERROR: {e}[/bold red]")
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)
