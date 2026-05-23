import streamlit as st
import time
import re

from models.llm_provider import LLMProvider
from agents.strategist import Strategist
from agents.researcher import Researcher
from agents.quant import Quant
from agents.executioner import Executioner
from brain import WarRoom, Verdict

# --- Page Config ---
st.set_page_config(
    page_title="The Iron Ledger | Chat",
    page_icon="💬",
    layout="centered"
)

# --- Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "name": "System",
            "content": "سلام! به **اتاق جنگ The Iron Ledger** خوش آمدی. من اینجا هستم تا ایده‌ت رو برای جنگ آماده کنم.\n\nابتدا لطفاً **ایده بیزنس** خودت رو کامل توضیح بده."
        }
    ]
if "phase" not in st.session_state:
    st.session_state.phase = "intake_idea"
if "idea_data" not in st.session_state:
    st.session_state.idea_data = {}

# --- CSS for specific elements ---
st.markdown("""
<style>
    .agent-name { font-weight: bold; color: #d35400; }
    .verdict-box { padding: 20px; border-radius: 10px; text-align: center; color: white; margin-top: 20px;}
</style>
""", unsafe_allow_html=True)

st.title("⚔️ The Iron Ledger")
st.markdown("*Survival of the fittest ideas.*")
st.divider()

# --- Display Active Models Sidebar ---
with st.sidebar:
    st.header("🤖 شبکه‌های عصبی فعال")
    st.markdown("سیستم واقعاً از **۴ هوش مصنوعی مجزا** (Multi-Agent) استفاده می‌کند. موتورهای پردازشی متصل شده:")
    try:
        temp_llm = LLMProvider()
        st.success(f"**🧠 استراتژیست:**\n`{temp_llm.models['strategist'].split('/')[-1]}`")
        st.info(f"**🔍 محقق (متصل به وب):**\n`{temp_llm.models['researcher'].split('/')[-1]}`")
        st.warning(f"**📊 کوانت (کدنویس):**\n`{temp_llm.models['quant'].split('/')[-1]}`")
        st.error(f"**⚔️ جلاد (منتقد):**\n`{temp_llm.models['executioner'].split('/')[-1]}`")
    except:
        st.markdown("*در حال اتصال به سرور...*")

# --- Display Chat History ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("name"):
            st.markdown(f"<span class='agent-name'>{msg['name']}</span>", unsafe_allow_html=True)
        st.write(msg["content"])

# --- User Intake & Chat Logic ---
if st.session_state.phase == "intake_idea":
    user_input = st.chat_input("پاسخ خود را اینجا بنویسید...")
    
    if user_input:
        # Display user message
        st.session_state.messages.append({"role": "user", "name": "You", "content": user_input})
        with st.chat_message("user"):
            st.markdown("<span class='agent-name'>You</span>", unsafe_allow_html=True)
            st.write(user_input)
            
        with st.spinner("در حال پردازش..."):
            try:
                llm = LLMProvider()
                sys_prompt = """تو نماینده بی‌رحم و جدی «اتاق جنگ بیزنس (The Iron Ledger)» هستی. وظیفه تو مصاحبه با کاربر است.
باید ۵ اطلاعات زیر را از او بگیری:
1. ایده بیزنس (توضیح)
2. بودجه اولیه (به دلار)
3. بازار هدف / کشور
4. مدل درآمدی
5. رقبای اصلی

قوانین:
- لحن تو سرد، کاملاً جدی و حرفه‌ای است. اینجا جای شوخی نیست.
- اگر کاربر پاسخ نامربوط داد (مثل "سلام"، "به تو چه"، "نمیدونم")، با جدیت به او اخطار بده که وقتت را تلف نکند و دوباره سوالت را بپرس.
- یکی یکی سوال بپرس تا کاربر گیج نشود. (مثلاً اول ایده رو کامل بپرس، بعد بودجه و...).
- وقتی تمام ۵ مورد به درستی مشخص شد، در انتهای پیامت دقیقاً عبارت [DATA_READY] را چاپ کن و سپس یک بلاک JSON با ساختار زیر بده:
```json
{
  "description": "...",
  "budget": 50000,
  "target_market": "...",
  "revenue_model": "...",
  "competitors": ["...", "..."]
}
```
"""
                # Build message history for LLM
                api_messages = [{"role": "system", "content": sys_prompt}]
                for m in st.session_state.messages:
                    # Pass user and assistant messages (ignore custom formatting names for API)
                    api_messages.append({"role": m["role"], "content": m["content"]})
                        
                # Call LLM
                response = llm.client.chat.completions.create(
                    model=llm.models["strategist"],
                    messages=api_messages,
                    temperature=0.7,
                    max_tokens=1000
                ).choices[0].message.content
                
                reply = response
                
                # Check if interview is complete
                if "[DATA_READY]" in response:
                    json_match = re.search(r'```(?:json)?\s*\n(.*?)\n\s*```', response, re.DOTALL)
                    if json_match:
                        import json
                        try:
                            # Cleanup and ensure budget is a number
                            parsed_data = json.loads(json_match.group(1))
                            if isinstance(parsed_data.get("budget"), str):
                                nums = re.findall(r'\d+', parsed_data["budget"].replace(',', ''))
                                parsed_data["budget"] = float(nums[0]) if nums else 50000.0
                                
                            st.session_state.idea_data = parsed_data
                            st.session_state.phase = "war_room_running"
                            reply = response.split("[DATA_READY]")[0].strip() + "\n\n🔥 **اطلاعات تکمیل شد. درهای اتاق جنگ در حال باز شدن است...**"
                        except Exception as parse_e:
                            reply = response.replace("[DATA_READY]", "").strip() + f"\n*(خطا در پردازش اطلاعات، لطفاً داده‌ها را دوباره چک کنید: {parse_e})*"
                    else:
                        reply = response.replace("[DATA_READY]", "").strip() + "\n*(سیستم نتوانست فایل نهایی را بخواند، لطفاً ادامه بدهید)*"

            except Exception as e:
                reply = f"خطای ارتباط با سرور هوش مصنوعی: {e}"

        # Display assistant reply
        st.session_state.messages.append({"role": "assistant", "name": "Interviewer", "content": reply})
        with st.chat_message("assistant"):
            st.markdown("<span class='agent-name'>Interviewer</span>", unsafe_allow_html=True)
            st.write(reply)

        st.rerun()

# --- Run War Room ---
if st.session_state.phase == "war_room_running":
    idea = st.session_state.idea_data
    
    # Initialize Agents
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
        st.error(f"خطا در اتصال به API: {e}")
        st.stop()

    analyses = []
    
    # Phase 1: Sequential but visible execution
    st.markdown("### 📡 در حال جمع‌آوری اطلاعات...")
    
    with st.status("مأمورها در حال کار روی ایده شما هستند...", expanded=True) as status:
        st.write(f"🧠 **The Visionary** *(پردازش با: {llm.models['strategist'].split('/')[-1]})* در حال ساخت مدل...")
        try:
            analyses.append(strategist.analyze(idea))
            st.write("✅ مدل تجاری ساخته شد.")
        except Exception as e: st.write(f"❌ خطای استراتژیست: {e}")
            
        st.write(f"🔍 **The Spy** *(پردازش با: {llm.models['researcher'].split('/')[-1]})* در حال جستجوی وب...")
        try:
            analyses.append(researcher.analyze(idea))
            st.write("✅ اطلاعات بازار جمع‌آوری شد.")
        except Exception as e: st.write(f"❌ خطای محقق: {e}")
            
        st.write(f"📊 **The Quant** *(پردازش با: {llm.models['quant'].split('/')[-1]})* در حال شبیه‌سازی مالی...")
        try:
            analyses.append(quant.analyze(idea))
            st.write("✅ شبیه‌سازی مالی تمام شد.")
        except Exception as e: st.write(f"❌ خطای ریاضیات: {e}")
            
        st.write(f"⚔️ **The Executioner** *(پردازش با: {llm.models['executioner'].split('/')[-1]})* در حال صدور کیفرخواست...")
        try:
            analyses.append(executioner.analyze(idea, prior_analyses=analyses))
            st.write("✅ کیفرخواست آماده شد.")
        except Exception as e: st.write(f"❌ خطای جلاد: {e}")
            
        status.update(label="✅ تحقیقات اولیه تمام شد!", state="complete", expanded=False)

    st.divider()

    # --- SHOW AGENT REPORTS (Clean & Minimalist) ---
    with st.chat_message("assistant"):
        st.markdown("<span style='color:#3498db; font-weight:bold;'>🤖 System</span>", unsafe_allow_html=True)
        st.write("✅ گزارش‌های فوق‌محرمانه مأمورها آماده شد.")
        
        with st.expander("📂 مشاهده جزئیات گزارش‌ها و کدهای پایتون (کلیک کنید)", expanded=False):
            tabs = st.tabs(["🧠 استراتژیست", "🔍 محقق", "📊 کوانت", "⚔️ جلاد"])
            names = ["strategist", "researcher", "quant", "executioner"]
            for i, analysis in enumerate(analyses):
                if i < len(tabs):
                    with tabs[i]:
                        model_name = llm.models.get(names[i], "Unknown").split('/')[-1]
                        st.caption(f"پردازشگر: {model_name}")
                        st.markdown(analysis.analysis)
                        
    # Add a minimal note to chat history
    st.session_state.messages.append({
        "role": "assistant", 
        "name": "System", 
        "content": "✅ گزارش‌های مأمورها تدوین شد. (جهت سادگی چت، در پوشه مخفی قرار گرفت)"
    })

    st.divider()

    # Phase 2: The Debate
    st.markdown("### 💬 مناظره زنده")
    
    with st.spinner("مأمورها در حال جنگ و بحث با یکدیگر هستند..."):
        debate_log = war_room.run_debate(analyses, idea)
        
    for msg in debate_log:
        role = "assistant"
        icon = "⚔️" if msg.sender == "executioner" else "🤖"
        color = "#e74c3c" if msg.message_type == "challenge" else "#2ecc71" if msg.message_type == "defense" else "#3498db"
        
        label = f"{icon} {msg.sender.upper()} [{msg.message_type}]"
        content = msg.content
        
        # Display in chat and save to session
        st.session_state.messages.append({"role": role, "name": label, "content": content})
        
        with st.chat_message(role):
            st.markdown(f"<span style='color:{color}; font-weight:bold;'>{label}</span>", unsafe_allow_html=True)
            st.write(content)

    # Phase 3: The Verdict
    st.divider()
    st.markdown("### ⚖️ حکم نهایی")
    
    with st.spinner("صدور رأی نهایی..."):
        verdict = war_room.evaluate_consensus(analyses)
        report = war_room.build_report(idea, verdict, analyses, debate_log)
        
    bg_color = "#2ecc71" if verdict == Verdict.APPROVED else "#e74c3c" if verdict == Verdict.REJECTED else "#f39c12"
    v_text = "تایید شد (APPROVED)" if verdict == Verdict.APPROVED else "رد شد (REJECTED)" if verdict == Verdict.REJECTED else "نیاز به اصلاح (NEEDS REVISION)"
    
    st.markdown(f"""
    <div class="verdict-box" style="background-color: {bg_color};">
        <h1>{v_text}</h1>
        <h3>امتیاز نهایی: {report.final_score}/10</h3>
        <h3>احتمال موفقیت مالی: {report.success_probability * 100:.1f}%</h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("#### 🔴 بزرگترین ریسک‌ها")
    for r in report.risk_analysis.get("critical_risks", [])[:3]: st.write(f"🔻 {r}")
        
    st.markdown("#### 🟢 نقاط قوت")
    for s in report.risk_analysis.get("strengths", [])[:3]: st.write(f"✅ {s}")

    st.markdown("#### 📋 توصیه‌های اتاق جنگ")
    for rec in report.recommendations: st.write(f"👉 {rec}")

    if report.financial_data:
        fin = report.financial_data
        st.info(f"💰 **ROI:** {fin.get('roi', 0):.1f}%  |  **میانگین سود:** ${fin.get('mean_profit', 0):,.0f}  |  **بدترین حالت:** ${fin.get('worst_case', 0):,.0f}")

    # End state
    st.session_state.phase = "finished"
    st.session_state.messages.append({
        "role": "assistant",
        "name": "System",
        "content": f"پرونده بسته شد. حکم نهایی: **{v_text}**. اگر می‌خواهی ایده جدیدی تست کنی، صفحه مرورگر را رفرش کن."
    })
    
    if st.button("تست ایده جدید"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
