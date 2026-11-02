"""Register Lockesmith's model prices in your LangFuse project, so its traces show cost.

    uv run python scripts/langfuse_prices.py

LangFuse matches a model call to a price by the call's model name. Ours carry LiteLLM's
"vertex_ai/" prefix and are newer than LangFuse's built-in list, so without this the traces
show tokens but no cost. Prices come from agent/pricing.py. Safe to rerun: a model that's
already defined is skipped. Needs LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY / LANGFUSE_BASE_URL
(in .env or the environment).
"""

import re
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402

from agent.pricing import PRICES, SOURCE  # noqa: E402



def main() -> int:
    load_dotenv()
    from langfuse import get_client
    from langfuse.api.commons.types.pricing_tier_input import PricingTierInput

    lf = get_client()
    if not lf.auth_check():
        print("LangFuse rejected the keys: check LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY and LANGFUSE_BASE_URL.")
        return 1
    # LangFuse allows one definition per name, so Gemini 3.8 Flash keeps its 2026 introductory
    # price here; it rises to $1.50 / $7.50 on 2027-01-01 (agent/pricing.py).
    existing, page = set(), 1
    while True:  # LangFuse's own built-in models come first, so read every page
        batch = lf.api.models.list(page=page, limit=100).data
        existing |= {m.model_name for m in batch}
        if len(batch) < 100:
            break
        page += 1
    for name, (inp, out) in PRICES.items():
        label = f"lockesmith-{name}"
        if label in existing:
            print(f"already defined: {label}")
            continue
        lf.api.models.create(
            model_name=label,
            match_pattern=f"(?i)^(vertex_ai/)?{re.escape(name)}$",
            unit="TOKENS",
            pricing_tiers=[PricingTierInput(name="Standard", is_default=True, priority=0, conditions=[],
                                            prices={"input": inp / 1_000_000, "output": out / 1_000_000})],
        )
        print(f"defined {label}: ${inp} / ${out} per 1M input / output tokens")
    print(f"Prices from {SOURCE}. They apply to traces recorded from now on.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
