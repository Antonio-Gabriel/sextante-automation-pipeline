"""Decision 3.27: the GitHub Actions pipelines, read from their files."""

import re
from pathlib import Path
from typing import Any, Final

import pytest
import yaml

WORKFLOWS: Final = Path(__file__).resolve().parents[3] / ".github" / "workflows"
PINNED: Final = re.compile(r"^[\w.-]+/[\w.-]+@[0-9a-f]{40}$")


def _workflow(name: str) -> dict[Any, Any]:
    loaded: dict[Any, Any] = yaml.safe_load((WORKFLOWS / name).read_text())
    return loaded


def _steps(workflow: dict[Any, Any]) -> list[dict[str, Any]]:
    return [step for job in workflow["jobs"].values() for step in job.get("steps", [])]


@pytest.mark.requirement("SEC-20", "D-3.27")
@pytest.mark.parametrize("name", ["ci.yml", "release.yml"])
def test_every_action_is_pinned_by_commit(name: str) -> None:
    """A moved tag of a third-party action never changes what runs with the secrets."""
    uses = [step["uses"] for step in _steps(_workflow(name)) if "uses" in step]

    assert uses and all(PINNED.match(action) for action in uses), uses


@pytest.mark.requirement("SEC-02", "D-3.27")
def test_ci_reads_no_secret_and_only_reads_the_repository() -> None:
    """Pull requests run it: nothing there can reach a secret or write."""
    text = (WORKFLOWS / "ci.yml").read_text()

    assert "secrets." not in text
    assert _workflow("ci.yml")["permissions"] == {"contents": "read"}


@pytest.mark.requirement("D-3.27")
def test_only_a_version_tag_releases_and_a_person_approves_production() -> None:
    """vX.Y.Z publishes X.Y.Z, after the full CI, behind the production environment."""
    release = _workflow("release.yml")
    jobs = release["jobs"]
    # PyYAML reads the key `on` as True.
    trigger = release[True]

    assert trigger == {"push": {"tags": ["v[0-9]+.[0-9]+.[0-9]+"]}}
    assert jobs["ci"]["uses"] == "./.github/workflows/ci.yml"
    assert jobs["publish"]["needs"] == "ci" and jobs["deploy"]["needs"] == "publish"
    assert jobs["deploy"]["environment"]["name"] == "production"
    assert release["concurrency"]["cancel-in-progress"] is False


@pytest.mark.requirement("D-3.27")
def test_the_published_image_carries_the_version_and_nothing_floating() -> None:
    """One tag per release, the version; no `latest` that would move under a deploy."""
    push = next(s for s in _steps(_workflow("release.yml")) if s.get("name") == "Build and push")
    tags = [line.strip() for line in push["with"]["tags"].splitlines() if line.strip()]

    assert tags == ["${{ vars.DOCKERHUB_REPOSITORY }}:${{ steps.version.outputs.version }}"]
    assert push["with"]["context"] == "build/shardcloud"
