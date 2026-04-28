"""
🤖 llm_provider.py — OpenRouter LLM Connection Layer
======================================================
Provides a unified interface to call different LLM models
through OpenRouter API (OpenAI-compatible).

Each agent can use a different model, configured via .env file.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


class LLMProvider:
    """
    Manages connections to OpenRouter API.
    Uses the OpenAI SDK since OpenRouter is OpenAI-compatible.

    Usage:
        llm = LLMProvider()
        response = llm.call("strategist", "Analyze this business idea...")
    """

    # OpenRouter base URL (replaces OpenAI's URL)
    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self):
        """Initialize the provider and load API key + model configs."""
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY not found in .env file!\n"
                "Get your key from: https://openrouter.ai/keys"
            )

        # One OpenAI client pointed at OpenRouter
        self.client = OpenAI(
            base_url=self.BASE_URL,
            api_key=self.api_key,
        )

        # Load model for each agent from .env
        self.models = {
            "strategist": os.getenv("STRATEGIST_MODEL", "inclusionai/ling-2.6-1t:free"),
            "researcher": os.getenv("RESEARCHER_MODEL", "inclusionai/ling-2.6-1t:free"),
            "quant": os.getenv("QUANT_MODEL", "inclusionai/ling-2.6-1t:free"),
            "executioner": os.getenv("EXECUTIONER_MODEL", "inclusionai/ling-2.6-1t:free"),
        }

        print("  🤖 LLM Provider initialized (OpenRouter)")
        for agent, model in self.models.items():
            print(f"     {agent:15s} → {model}")

    def call(
        self,
        agent_name: str,
        user_message: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """
        Send a message to the LLM assigned to a specific agent.

        Args:
            agent_name: Which agent is calling (strategist, researcher, etc.)
            user_message: The main prompt/question
            system_prompt: The agent's personality/instructions
            temperature: Creativity level (0.0 = strict, 1.0 = creative)
            max_tokens: Max response length

        Returns:
            The LLM's text response
        """
        model = self.models.get(agent_name, "inclusionai/ling-2.6-1t:free")

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""

        except Exception as e:
            error_msg = f"[LLM ERROR for {agent_name}] {type(e).__name__}: {e}"
            print(f"  ❌ {error_msg}")
            return error_msg

    def call_with_history(
        self,
        agent_name: str,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """
        Send a full conversation history to the LLM.
        Useful for the debate phase where context matters.

        Args:
            agent_name: Which agent is calling
            messages: List of {"role": "system"|"user"|"assistant", "content": "..."}
            temperature: Creativity level
            max_tokens: Max response length

        Returns:
            The LLM's text response
        """
        model = self.models.get(agent_name, "inclusionai/ling-2.6-1t:free")

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""

        except Exception as e:
            error_msg = f"[LLM ERROR for {agent_name}] {type(e).__name__}: {e}"
            print(f"  ❌ {error_msg}")
            return error_msg


# ---------------------------------------------------------------------------
#  Quick Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n  Testing OpenRouter connection...\n")
    llm = LLMProvider()

    # Quick test with one agent
    response = llm.call(
        agent_name="strategist",
        user_message="Say 'Connection successful!' in one sentence.",
        system_prompt="You are a helpful assistant. Reply briefly.",
        max_tokens=50,
    )
    print(f"\n  Response: {response}")
