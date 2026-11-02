"""Model prices, for the cost of each request (in /chat's usage, the trace panel and the README)
and for LangFuse (scripts/langfuse_prices.py registers them, since its built-in list doesn't
match LiteLLM's "vertex_ai/" names).

USD per 1M tokens, Vertex AI global endpoint, standard tier, prompts up to 200K tokens; output
includes reasoning ("thinking") tokens. Read from https://cloud.google.com/vertex-ai/generative-ai/pricing
on 2026-11-01. Gemini 3.8 Flash is at its introductory price through 2026-12-31, then $1.50 / $7.50.
"""

SOURCE = "https://cloud.google.com/vertex-ai/generative-ai/pricing (read 2026-11-01)"
PRICES = {  # model -> (input, output) per 1M tokens
    "gemini-3.5-flash": (1.50, 9.00),
    "gemini-3.1-pro-preview": (2.00, 12.00),
    "gemini-3.8-flash": (0.75, 3.75),
}


def base_name(model: str) -> str:
    """"vertex_ai/gemini-3.5-flash" -> "gemini-3.5-flash"."""
    return model.rsplit("/", 1)[-1]


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float | None:
    """None for a model without a known price (e.g. after switching to Claude)."""
    price = PRICES.get(base_name(model))
    if price is None:
        return None
    return round((input_tokens * price[0] + output_tokens * price[1]) / 1_000_000, 6)
