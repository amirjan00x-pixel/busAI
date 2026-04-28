"""
🌐 app.py — The Iron Ledger Web UI (Streamlit)
================================================
A beautiful Web UI for The Iron Ledger War Room.
Run with: streamlit run app.py
"""

import streamlit as st
import concurrent.futures
import time

from models.llm_provider import LLMProvider
from agents.strategist import Strategist
from agents.researcher import Researcher
from agents.quant import Quant
from agents.executioner import Executioner
from brain import WarRoom, Verdict

# --- Page Config ---
st.set_page_config(
    page_title="The Iron Ledger | War Room",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Styling ---
st.markdown("""
<style>
    .verdict-approved { background-color: #1e3a1e; border: 2px solid #2e8b57; padding: 20px; border-radius: 10px; text-align: center; }
    .verdict-rejected { background-color: #3a1e1e; border: 2px solid #8b0000; padding: 20px; border-radius: 10px; text-align: center; }
    .verdict-revision { background-color: #3a381e; border: 2px solid #b8860b; padding: 20px; border-radius: 10px; text-align: center; }
    .stAlert { margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# --- Helpers ---
def display_agent_analysis(analysis, icon, title):
    with st.expander(f"{icon} {title} (Score: {analysis.score}/10)", expanded=True):
        st.markdown(f"**Final Score:** `{analysis.score}/10`")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("🔴 **Key Risks**")
            for risk in analysis.key_risks[:3]:
                st.write(f"- {risk}")
        with col2:
            st.markdown("🟢 **Key Strengths**")
            for strength in analysis.key_strengths[:3]:
                st.write(f"- {strength}")
                
        st.divider()
        st.markdown("📝 **Full Analysis**")
        st.info(analysis.analysis)


# --- Main UI ---
st.title("⚔️ THE IRON LEDGER: WAR ROOM")
st.markdown("Submit your business idea. 4 ruthless AI agents will dissect it, simulate it, and try to **DESTROY** it.")

# --- Sidebar Intake Form ---
with st.sidebar:
    st.header("📋 Idea Intake Form")
    with st.form("intake_form"):
        description = st.text_area("💡 Describe your business idea", height=150)
        budget = st.number_input("💰 Initial budget (USD)", value=50000, step=5000)
        target_market = st.text_input("🌍 Target market / country", value="Global")
        revenue_model = st.text_input("💳 Revenue model", value="Subscription")
        competitors_str = st.text_input("🏢 Known competitors", value="None")
        
        submitted = st.form_submit_button("🔥 START WAR ROOM", use_container_width=True)

# --- Execution Pipeline ---
if submitted:
    if not description.strip():
        st.error("Please describe your business idea first!")
        st.stop()

    idea = {
        "description": description,
        "budget": budget,
        "target_market": target_market,
        "revenue_model": revenue_model,
        "competitors": [c.strip() for c in competitors_str.split(",") if c.strip() and c.lower() != 'none']
    }

    st.divider()

    # Initialization
    try:
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
        st.error(f"Failed to initialize systems: {e}")
        st.stop()

    # --- PHASE 1: Intelligence Gathering ---
    st.header("📡 Phase 1: Intelligence Gathering")
    
    analyses = []
    
    with st.spinner("🤖 Visionary, Spy, and Quant are analyzing simultaneously (this may take up to 45s)..."):
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            f_strat = executor.submit(strategist.analyze, idea)
            f_res = executor.submit(researcher.analyze, idea)
            f_quant = executor.submit(quant.analyze, idea)
            
            # Strategist
            try:
                strat_res = f_strat.result()
                analyses.append(strat_res)
            except Exception as e:
                st.error(f"Strategist failed: {e}")
                
            # Researcher
            try:
                res_res = f_res.result()
                analyses.append(res_res)
            except Exception as e:
                st.error(f"Researcher failed: {e}")
                
            # Quant
            try:
                quant_res = f_quant.result()
                analyses.append(quant_res)
            except Exception as e:
                st.error(f"Quant failed: {e}")

    # Display Phase 1 results
    col1, col2, col3 = st.columns(3)
    with col1:
        if len(analyses) > 0: display_agent_analysis(analyses[0], "🧠", "The Visionary")
    with col2:
        if len(analyses) > 1: display_agent_analysis(analyses[1], "🔍", "The Spy")
    with col3:
        if len(analyses) > 2: display_agent_analysis(analyses[2], "📊", "The Quant")

    # Executioner Phase
    st.header("⚔️ The Executioner Enters")
    with st.spinner("The Executioner is reviewing the data and preparing the kill shots..."):
        try:
            exec_res = executioner.analyze(idea, prior_analyses=analyses)
            analyses.append(exec_res)
            display_agent_analysis(exec_res, "⚔️", "The Executioner")
        except Exception as e:
            st.error(f"Executioner failed: {e}")

    # --- PHASE 2: Debate ---
    if len(analyses) >= 3:
        st.header("💬 Phase 2: The Debate")
        with st.spinner("Agents are debating..."):
            debate_log = war_room.run_debate(analyses, idea)
            
            for msg in debate_log:
                role = "assistant" if msg.sender == "executioner" else "user"
                avatar = "⚔️" if msg.sender == "executioner" else "🧠"
                
                with st.chat_message(role, avatar=avatar):
                    st.markdown(f"**{msg.sender.upper()}** ({msg.message_type}):")
                    st.write(msg.content)
    else:
        debate_log = []

    # --- PHASE 3: Verdict ---
    st.header("⚖️ Final Judgment")
    with st.spinner("Calculating final verdict..."):
        verdict = war_room.evaluate_consensus(analyses)
        report = war_room.build_report(idea, verdict, analyses, debate_log)
        
        v_class = ""
        v_icon = ""
        v_text = ""
        if verdict == Verdict.APPROVED:
            v_class = "verdict-approved"
            v_icon = "✅"
            v_text = "IDEA APPROVED"
        elif verdict == Verdict.REJECTED:
            v_class = "verdict-rejected"
            v_icon = "💀"
            v_text = "IDEA REJECTED"
        else:
            v_class = "verdict-revision"
            v_icon = "🔄"
            v_text = "NEEDS REVISION / NO CONSENSUS"

        st.markdown(f"""
        <div class="{v_class}">
            <h1>{v_icon} {v_text}</h1>
            <h3>Score: {report.final_score}/10 | Probability: {report.success_probability*100:.1f}%</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Financial Metrics
        if report.financial_data:
            st.subheader("💰 Financial Summary")
            m1, m2, m3, m4 = st.columns(4)
            fin = report.financial_data
            if "roi" in fin: m1.metric("ROI", f"{fin['roi']:.1f}%")
            if "mean_profit" in fin: m2.metric("Mean Profit", f"${fin['mean_profit']:,.0f}")
            if "worst_case" in fin: m3.metric("Worst Case (5%)", f"${fin['worst_case']:,.0f}")
            if "break_even_months" in fin: m4.metric("Break-Even", f"{fin['break_even_months']} mo")

        st.divider()
        
        # Recommendations
        st.subheader("📋 Final Recommendations")
        for rec in report.recommendations:
            st.write(rec)
            
        st.balloons() if verdict == Verdict.APPROVED else None
