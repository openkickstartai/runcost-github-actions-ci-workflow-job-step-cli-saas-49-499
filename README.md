# RunCost — GitHub Actions Cost Analyzer & Optimizer

> Turn invisible CI bills into actionable savings. Break down costs to every workflow/job/step and get automated optimization recommendations.

## 🔥 The Problem

GitHub Actions billing is a black box. Teams routinely waste 30-50% of CI spend on:
- Uncached dependency installs (3min/run × 200 runs/month = $$$)
- Oversized runners for lightweight jobs
- Redundant builds on non-code changes
- No visibility into per-workflow costs

## 🚀 Quick Start

```bash
pip install -r requirements.txt
export GITHUB_TOKEN=ghp_your_token_here

# Analyze last 50 runs
python runcost.py owner/repo

# JSON output for dashboards
python runcost.py owner/repo --json

# Analyze more history
python runcost.py owner/repo --limit 100
```

## 📊 Example Output

```
==================================================
  RunCost Report — acme/backend
==================================================
  Total runs analyzed: 47
  Total estimated cost: $23.41

  📦 CI Pipeline
     Runs: 32  |  Minutes: 412.3  |  Cost: $18.20
       └─ build: 32 runs, 287.1min, $12.50
       └─ test: 32 runs, 125.2min, $5.70

  💡 Optimization Recommendations
  💸 [expensive_workflow] CI Pipeline
     Cache deps, split jobs, use cheaper runners. Potential saving: 20-40%.
  🐌 [long_job] CI Pipeline / build
     Enable caching, parallelize steps. Potential saving: 15-30%.
```

## 💰 Pricing

| Feature | Free | Pro ($49/mo) | Enterprise ($499/mo) |
|---|---|---|---|
| Cost breakdown by workflow | ✅ | ✅ | ✅ |
| Job/step level analysis | ✅ | ✅ | ✅ |
| Optimization recommendations | ✅ | ✅ | ✅ |
| JSON export | ✅ | ✅ | ✅ |
| Repos analyzed | 3 | Unlimited | Unlimited |
| Historical analysis | 50 runs | 1 year | Unlimited |
| Slack/Teams alerts | ❌ | ✅ | ✅ |
| Budget enforcement (block PR) | ❌ | ✅ | ✅ |
| Anomaly detection | ❌ | ✅ | ✅ |
| PDF reports for management | ❌ | ❌ | ✅ |
| Cost allocation by team | ❌ | ❌ | ✅ |
| SOC2 audit trail | ❌ | ❌ | ✅ |
| SSO / SAML | ❌ | ❌ | ✅ |
| SLA & support | Community | Email | Dedicated |

## 📈 Why Pay?

- **Teams spending >$200/mo on Actions** save 30-50% with Pro recommendations
- **VP Engineering / CFO** need PDF cost reports and team-level allocation
- **Budget enforcement** blocks PRs that would blow the CI budget
- **Anomaly detection** catches a rogue workflow burning $500 overnight
- ROI: $49/mo Pro pays for itself if it saves you just 1 hour of CI time

## 🔒 Security

- Token never logged or stored — validated format, masked in output
- All inputs validated against injection (repo path, run IDs)
- Read-only GitHub API access (only needs `actions:read` scope)
- No data sent to third parties

## License

MIT — Free CLI forever. Pro/Enterprise features require a license key.
