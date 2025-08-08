from lib.jira_service_management.config import JIRA_SERVICE_MANAGEMENT_FILTER_TEAM, JIRA_SERVICE_MANAGEMENT_FILTER_USERS


def filter_users(users: list[dict]) -> list[dict]:
    """Apply filters to users."""
    if JIRA_SERVICE_MANAGEMENT_FILTER_TEAM:
        filtered_users = []
        for u in users:
            if any(t["id"] == JIRA_SERVICE_MANAGEMENT_FILTER_TEAM for t in u["teams"]):
                filtered_users.append(u)
        users = filtered_users

    if JIRA_SERVICE_MANAGEMENT_FILTER_USERS:
        users = [u for u in users if u["id"] in JIRA_SERVICE_MANAGEMENT_FILTER_USERS]

    return users
