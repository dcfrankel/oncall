from typing import List

from lib.jira_service_management.config import (
    JIRA_SERVICE_MANAGEMENT_FILTER_TEAM,
)


def filter_teams(teams: list[dict]) -> list[dict]:
    """Apply filters to teams."""
    if JIRA_SERVICE_MANAGEMENT_FILTER_TEAM:
        teams = [
            t for t in teams if t.get("teamId") == JIRA_SERVICE_MANAGEMENT_FILTER_TEAM
        ]
    return teams


def match_team(team: dict, oncall_teams: List[dict]) -> None:
    """
    Match Jira Service Management team with Grafana OnCall team.
    """
    oncall_team = None
    for candidate in oncall_teams:
        name = team["displayName"].lower().strip()
        if name == candidate["name"].lower().strip():
            oncall_team = candidate
    team["oncall_team"] = oncall_team
