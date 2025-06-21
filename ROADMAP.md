# Roadmap

We will be attacking this on two fronts:

**Step one:** create a prototype app that relies on free, open-source LLMs

- This lets us iterate on ideas fast without wasting any of our precious credits
- We want a working, fully functional pipeline that we will implement step by step:
  1. Vanilla prompting (no system prompt), toolless
     - No need to iterate heavily on different prompts for now since we will need to assess the results on the actual OpenAI LLM later
  2. Implement function/tool-calling and active testing
     - Start with one essential Football API endpoint for testing
     - Add them one by one and test them out
  3. Add basic prompt history and context if needed.
  4. If we have the time we'll try adding a minimalistic guardrail LLM to prevent prompt injection
     - <https://huggingface.co/protectai/deberta-v3-base-prompt-injection-v2> should be good enough for this demo
     - We can further test this using something like <https://github.com/utkusen/promptmap>
     - We will be switching this for OpenAI's approach anyway so it might not be worth our time

[Langchain](https://www.langchain.com/) or [LangGraph](https://www.langchain.com/langgraph) should be more than enough for this purpose.

We'll also use [Arize Phoenix](https://github.com/Arize-ai/phoenix) for observability incl. debugging, evaluation, token counting and optimization.

**Step two:** once our pipeline is well established, tested and working we will switch to OpenAI's endpoints and/or API

- A good prompt should be enough to defer questions about other sports but if it's not we'll try adding a conditional edge for safety

Let's get to work!
