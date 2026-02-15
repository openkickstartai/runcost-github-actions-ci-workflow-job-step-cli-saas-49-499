#!/usr/bin/env python3
"""RunCost CLI — GitHub Actions cost analysis & optimization."""
import argparse
import json
import os
import sys

from engine import Client, analyze, validate_repo


def mask_token(token):
    """Mask token for safe display — never show full credentials."""
    if len(token) > 8:
        return token[:4] + "*" * (len(token) - 8) + token[-4:]
    return "****"


def print_table(workflows):
    """Print cost breakdown table."""
    if not workflows:
        print("  (no workflow data)")
        return
    for name, wf in sorted(workflows.items(), key=lambda x: -x[1]["cost"]):
        print(f"\n  \U0001f4e6 {name}")
        print(f"     Runs: {wf['runs']}  |  Minutes: {wf['minutes']:.1f}  |  Cost: ${wf['cost']:.2f}")
        for jn, j in sorted(wf.get("jobs", {}).items(), key=lambda x: -x[1]["cost"]):
            print(f"       \u2514\u2500 {jn}: {j['count']} runs, {j['minutes']:.1f}min, ${j['cost']:.2f}")


def print_recs(recs):
    """Print optimization recommendations."""
    if not recs:
        print("  \u2705 No optimization issues found — your CI is lean!")
        return
    icons = {"expensive_workflow": "\U0001f4b8", "long_job": "\U0001f40c", "high_frequency": "\U0001f504"}
    for r in recs:
        label = r.get("workflow", "")
        if "job" in r:
            label += f" / {r['job']}"
        print(f"  {icons.get(r['type'], '\u26a0\ufe0f')} [{r['type']}] {label}")
        print(f"     {r['fix']}")


def main():
    parser = argparse.ArgumentParser(description="RunCost \u2014 GitHub Actions cost analyzer")
    parser.add_argument("repo", help="GitHub repository (owner/repo)")
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"),
                        help="GitHub token (or set GITHUB_TOKEN env)")
    parser.add_argument("--limit", type=int, default=50, help="Max runs to analyze (default: 50)")
    parser.add_argument("--json", dest="as_json", action="store_true", help="Output JSON")
    parser.add_argument("--api-url", default="https://api.github.com", help=argparse.SUPPRESS)
    args = parser.parse_args()

    if not args.token:
        print("\u274c Set GITHUB_TOKEN env or use --token", file=sys.stderr)
        sys.exit(1)
    try:
        validate_repo(args.repo)
    except ValueError as e:
        print(f"\u274c {e}", file=sys.stderr)
        sys.exit(1)

    print(f"\U0001f50d Analyzing {args.repo} (last {args.limit} runs)...")
    print(f"\U0001f511 Token: {mask_token(args.token)}")

    try:
        client = Client(args.token, args.api_url)
        result = analyze(client, args.repo, args.limit)
    except Exception as e:
        print(f"\u274c Analysis failed: {e}", file=sys.stderr)
        sys.exit(1)

    if args.as_json:
        print(json.dumps(result, indent=2, default=str))
        return

    sep = "=" * 52
    print(f"\n{sep}")
    print(f"  RunCost Report \u2014 {args.repo}")
    print(sep)
    print(f"  Total runs analyzed: {result['total_runs']}")
    print(f"  Total estimated cost: ${result['total_cost']:.2f}")
    print(f"\n{'\u2500' * 52}")
    print("  \U0001f4ca Cost Breakdown by Workflow")
    print_table(result["workflows"])
    print(f"\n{'\u2500' * 52}")
    print("  \U0001f4a1 Optimization Recommendations")
    print_recs(result["recommendations"])
    print(f"{sep}")
    print("  \U0001f680 RunCost Pro: Slack alerts, budget enforcement,")
    print("     anomaly detection. https://runcost.dev/pricing")
    print(f"{sep}\n")


if __name__ == "__main__":
    main()
