from typing import List

from lib.jira_service_management.config import (
    JIRA_SERVICE_MANAGEMENT_FILTER_TEAM,
)


def filter_teams(teams: list[dict], schedules: list[dict] = None, integrations: list[dict] = None) -> list[dict]:
    """
    Apply filters to teams.
    
    Args:
        teams: List of teams to filter
        schedules: List of schedules to check for team association
        integrations: List of integrations to check for team association
    
    Returns:
        Filtered list of teams that either:
        - Match the JIRA_SERVICE_MANAGEMENT_FILTER_TEAM if set
        - Have associated escalations, schedules, or integrations
    """
    filtered_teams = []
    
    # First apply the team filter if configured
    if JIRA_SERVICE_MANAGEMENT_FILTER_TEAM:
        teams = [
            t for t in teams if t.get("teamId") == JIRA_SERVICE_MANAGEMENT_FILTER_TEAM
        ]
    
    # Then filter based on associated resources
    for team in teams:
        has_escalations = len(team.get("escalations", [])) > 0
        
        has_schedules = False
        if schedules:
            for schedule in schedules:
                if schedule["teamId"] == team["teamId"]:
                    has_schedules = True
                    break
        
        has_integrations = False
        if integrations:
            for integration in integrations:
                if integration["teamId"] == team["teamId"]:
                    has_integrations = True
                    break
        
        if has_escalations or has_schedules or has_integrations:
            filtered_teams.append(team)
    
    return filtered_teams


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
