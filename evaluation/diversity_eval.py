"""
Simple diversity evaluation script for the meal planner API.

Mirrors the frontend evaluation logic:
- Modes: llm_only, rag, hybrid
- Durations: 1, 3, 5, 7 days
- Runs per (mode, duration) configuration: configurable (default 3)

For each configuration, it:
- Calls POST /api/generate-meal-plan multiple times
- Collects all recipe_name values
- Computes diversity score = unique_meals / total_meals * 100
"""

import argparse
import os
from typing import Dict, List

import httpx


EVAL_MODES = ["llm_only", "rag", "hybrid"]
EVAL_DURATIONS = [1, 3, 5, 7]


def get_user_id() -> str:
    """Simple deterministic user_id so runs group together server-side."""
    return os.getenv("EVAL_USER_ID", "eval-user-cli")


def evaluate_config(
    client: httpx.Client,
    api_url: str,
    mode: str,
    days: int,
    runs: int,
) -> Dict:
    """Run evaluation for a single (mode, days) configuration."""
    meal_names: List[str] = []
    user_id = get_user_id()

    for _ in range(runs):
        query = f"Create a {days}-day healthy, diverse meal plan"
        payload = {
            "query": query,
            "generation_mode": mode,
            "user_id": user_id,
        }
        resp = client.post(f"{api_url}/api/generate-meal-plan", json=payload, timeout=90.0)
        resp.raise_for_status()
        data = resp.json()

        for day_obj in data.get("meal_plan", []):
            for meal in day_obj.get("meals", []):
                name = str(meal.get("recipe_name", "")).strip().lower()
                if name:
                    meal_names.append(name)

    total_meals = len(meal_names)
    unique_meals = len(set(meal_names))
    diversity_score = round((unique_meals / total_meals) * 100) if total_meals else 0

    return {
        "mode": mode,
        "days": days,
        "runs": runs,
        "total_meals": total_meals,
        "unique_meals": unique_meals,
        "diversity_score": diversity_score,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run diversity evaluation against the Meal Planner API.")
    parser.add_argument(
        "--api-url",
        default=os.getenv("API_URL", "http://localhost:8000"),
        help="Base URL of the API (default: %(default)s or API_URL env var).",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=int(os.getenv("EVAL_RUNS_PER_CONFIG", "3")),
        help="Number of runs per (mode, days) configuration (default: %(default)s).",
    )
    args = parser.parse_args()

    api_url = args.api_url.rstrip("/")
    runs = max(1, args.runs)

    print(f"Using API: {api_url}")
    print(f"Runs per configuration: {runs}")
    print()

    results: List[Dict] = []

    with httpx.Client() as client:
        total_configs = len(EVAL_MODES) * len(EVAL_DURATIONS)
        idx = 0
        for mode in EVAL_MODES:
            for days in EVAL_DURATIONS:
                idx += 1
                print(f"[{idx}/{total_configs}] Evaluating mode={mode}, days={days} ...", flush=True)
                try:
                    res = evaluate_config(client, api_url, mode, days, runs)
                    results.append(res)
                    print(
                        f"  -> total_meals={res['total_meals']}, "
                        f"unique_meals={res['unique_meals']}, "
                        f"diversity={res['diversity_score']}%"
                    )
                except Exception as e:
                    print(f"  !! Failed for mode={mode}, days={days}: {e}")
                print()

    print("\n=== Summary ===")
    header = f"{'MODE':<10} {'DAYS':<4} {'RUNS':<4} {'TOTAL':<6} {'UNIQUE':<7} {'DIVERSITY':<9}"
    print(header)
    print("-" * len(header))
    for res in sorted(results, key=lambda r: (r["mode"], r["days"])):
        print(
            f"{res['mode']:<10} {res['days']:<4} {res['runs']:<4} "
            f"{res['total_meals']:<6} {res['unique_meals']:<7} {res['diversity_score']}%"
        )


if __name__ == "__main__":
    main()


