"""
RECOMMEND + NARRATE stage.

Takes the anomaly summary (from detect.py) and evidence bundle (from
correlate.py) and asks Claude to produce:
  - a one-paragraph plain-language explanation of the KPI move
  - 2-3 ranked next steps
  - an explicit confidence / uncertainty flag when evidence is ambiguous

Falls back to a deterministic template if no ANTHROPIC_API_KEY is set,
so the demo still runs end-to-end offline.
"""
import os
import json

SYSTEM_PROMPT = """You are the narration layer of "InsightForge", a KPI Storytelling \
Engine that explains business metric shifts in plain language for time-pressed \
executives. You are given (1) a statistical summary of a detected KPI anomaly and \
(2) a bundle of correlated structured and unstructured evidence (support tickets, \
inventory/pricing events, news headlines).

Write a brief with exactly this structure, as JSON:
{
  "headline": "<one sentence, <25 words, stating what happened and the likely cause>",
  "explanation": "<2-4 sentences in plain business language, citing the concrete evidence>",
  "confidence": "<High | Medium | Low>",
  "confidence_reason": "<one sentence on why>",
  "recommended_actions": ["<action 1>", "<action 2>", "<optional action 3>"]
}

Rules:
- Ground every claim in the evidence provided. Do not invent facts not present in the data.
- If evidence is thin, ambiguous, or conflicting, say so explicitly and lower confidence \
  rather than guessing at a cause.
- Keep the tone crisp and decision-ready, like a analyst brief for a VP, not a chatbot.
- Output ONLY the JSON object, no markdown fences, no preamble.
"""


def _build_user_prompt(incident: dict, evidence: dict, persona: str) -> str:
    return f"""KPI ANOMALY SUMMARY:
{json.dumps(incident, indent=2)}

CORRELATED EVIDENCE:
{json.dumps(evidence, indent=2)}

PERSONA: {persona}
Tailor the brief for this persona. For Sales Manager, emphasize operational explanation,
inventory focus, ticket spike, and immediate actions. For Regional Director, emphasize
executive summary, revenue impact, business drivers, and strategic recommendations.

Write the brief now."""


def _fallback_brief(incident: dict, evidence: dict, persona: str) -> dict:
    """Deterministic, evidence-grounded brief used when no API key is configured."""
    direction = incident.get("direction", "shift")
    pct = incident.get("avg_pct_vs_trend", 0)
    region = evidence.get("region", "the region")
    events = evidence.get("structured_events", [])
    ticket_ratio = evidence.get("ticket_spike_ratio", 1)

    event_bits = "; ".join(e["detail"] for e in events) if events else "no structured events logged in this window"
    confidence = "High" if events and ticket_ratio >= 2 else ("Medium" if events else "Low")

    if persona == "Sales Manager":
        headline = f"{region} revenue {direction} of {abs(pct):.1f}% vs. trend; investigate inventory and ticket signals immediately."
        explanation_prefix = "Operationally,"
        actions = [
            "Check inventory availability and expedite resolution of the logged event." if events else
            "Inspect inventory and operational logs for the incident window.",
            "Review the ticket spike and monitor customer impact through recovery.",
            "Escalate unresolved operational blockers to regional operations.",
        ]
    else:
        headline = f"{region} revenue {direction} of {abs(pct):.1f}% vs. trend, with {len(events)} corroborating business driver(s)."
        explanation_prefix = "Executive summary:"
        actions = [
            "Assess the revenue impact and align regional leaders on the likely business drivers.",
            "Review pricing, inventory, and competitor signals before making strategic adjustments.",
            "Track recovery and escalate if the revenue variance persists.",
        ]

    return {
        "headline": headline,
        "explanation": (
            f"{explanation_prefix} In the window {evidence['window']['start']} to {evidence['window']['end']}, {region} revenue "
            f"moved {pct:+.1f}% against its expected trend. Support ticket volume ran "
            f"{ticket_ratio}x the regional baseline, with the most common terms being "
            f"{', '.join(evidence.get('top_ticket_terms', [])[:4]) or 'none flagged'}. "
            f"Logged events in this window: {event_bits}."
        ),
        "confidence": confidence,
        "confidence_reason": (
            "Structured events and a matching ticket spike both point to the same window and region."
            if confidence == "High" else
            "Some corroborating signal exists but it's not conclusive on its own."
            if confidence == "Medium" else
            "No structured events logged in this window — treat this as an open anomaly, not an explained one."
        ),
        "recommended_actions": actions,
    }


def generate_brief(incident: dict, evidence: dict, persona: str = "Regional Director") -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        result = _fallback_brief(incident, evidence, persona)
        result["_source"] = "offline_fallback (set ANTHROPIC_API_KEY to use Claude)"
        return result

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=800,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _build_user_prompt(incident, evidence, persona)}],
        )
        text = "".join(block.text for block in msg.content if block.type == "text").strip()
        text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        result = json.loads(text)
        result["_source"] = "claude"
        return result
    except Exception as e:
        result = _fallback_brief(incident, evidence, persona)
        result["_source"] = f"offline_fallback (Claude call failed: {e})"
        return result
