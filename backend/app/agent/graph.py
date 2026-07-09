"""
The LangGraph agent that manages HCP interactions end to end.

Role of this agent: it sits between the sales rep's natural-language input
(typed in the "AI Assistant" chat panel) and the structured Interaction
records in the database. Instead of the rep filling out every form field by
hand, they can describe what happened in plain language, and the agent
decides which tool(s) to call — logging a brand-new interaction, editing one
that already exists, looking up history for an HCP, summarizing a
relationship, or suggesting next steps — using the LLM (Groq / gemma2-9b-it)
both for that tool selection and for turning free text into structured data
inside the tools themselves.

We use LangGraph's prebuilt `create_react_agent`, which implements the
standard ReAct loop (think -> call tool -> observe -> repeat) as a small
state graph, plus an in-memory checkpointer so a conversation (keyed by
thread_id) keeps context across turns — e.g. "log a meeting with Dr. Smith"
followed by "actually make that sentiment negative" without repeating the ID.
"""

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage

from app.agent.llm import get_llm
from app.agent.tools import ALL_TOOLS

SYSTEM_PROMPT = """You are the AI Assistant embedded in a pharma sales rep's CRM, on the \
"Log HCP Interaction" screen. Your job is to help the rep record and manage their \
interactions with Healthcare Professionals (HCPs) through natural conversation, as an \
alternative to filling out the structured form by hand.

You have five tools:
- log_interaction: save a brand-new interaction from a free-text description.
- edit_interaction: change an interaction that's already been logged.
- search_interactions: find past interactions by HCP name or topic.
- summarize_hcp_history: brief the rep on their history with a given HCP.
- suggest_follow_up_actions: propose next steps for a specific interaction.

Guidelines:
- When the rep describes a new meeting/call/email, call log_interaction with their \
description passed through mostly as-is — the tool itself uses an LLM to pull out \
structured fields, so don't over-engineer the input.
- When the rep asks to change something about an interaction they just logged or \
mentioned, use search_interactions first if you don't have the ID, then call \
edit_interaction.
- Keep replies short and conversational — you're a sidebar assistant, not a report \
generator. Confirm what you did in one or two sentences.
- Never invent data. If a tool call fails or a field is genuinely unknown, say so \
plainly and ask the rep for the missing detail.
"""

_checkpointer = MemorySaver()
_agent = None


def get_agent():
    """Builds (once) and returns the compiled LangGraph agent."""
    global _agent
    if _agent is None:
        llm = get_llm()
        _agent = create_react_agent(
            llm,
            tools=ALL_TOOLS,
            prompt=SYSTEM_PROMPT,
            checkpointer=_checkpointer,
        )
    return _agent


def run_agent_turn(message: str, thread_id: str = "default") -> dict:
    """
    Runs one turn of the conversation and returns the assistant's reply plus
    a simplified log of any tool calls made, so the frontend can show what
    the agent actually did (useful for the demo video).
    """
    agent = get_agent()
    config = {"configurable": {"thread_id": thread_id}}
    result = agent.invoke({"messages": [HumanMessage(content=message)]}, config=config)

    messages = result["messages"]
    reply = ""
    tool_calls = []

    for msg in messages:
        msg_type = msg.__class__.__name__
        if msg_type == "AIMessage":
            if getattr(msg, "content", None):
                reply = msg.content
            for tc in getattr(msg, "tool_calls", None) or []:
                tool_calls.append({"tool": tc["name"], "args": tc["args"]})
        elif msg_type == "ToolMessage":
            # attach the tool's result to the matching call, if we can find one
            for tc in tool_calls:
                if "result" not in tc:
                    tc["result"] = msg.content
                    break

    return {"reply": reply, "tool_calls": tool_calls}
