from re import A
from lib.common.report import TAB
from lib.common.resources.users import match_user
from lib.oncall.api_client import OnCallAPIClient
from lib.grafana.api_client import SvcGrafanaAPIClient
from lib.jira_service_management.api_client import JiraServiceManagementAPIClient
from lib.jira_service_management.config import (
    MIGRATE_USERS,
    MODE,
    MODE_PLAN,
    UNSUPPORTED_INTEGRATION_TO_WEBHOOKS,
    ASSOCIATE_TEAMS,
    GRAFANA_SERVICE_ACCOUNT_TOKEN,
    GRAFANA_URL
)
from lib.jira_service_management.report import (
    escalation_policy_report,
    format_escalation_policy,
    format_integration,
    format_schedule,
    format_team,
    integration_report,
    schedule_report,
    team_report,
    user_report,
)
from lib.jira_service_management.resources.escalation_policies import (
    filter_escalation_policies,
    match_escalation_policy,
    match_users_and_schedules_for_escalation_policy,
    migrate_escalation_policy,
)
from lib.jira_service_management.resources.integrations import (
    filter_integrations,
    match_integration,
    migrate_integration,
)
from lib.jira_service_management.resources.schedules import (
    filter_schedules,
    match_schedule,
    match_users_for_schedule,
    migrate_schedule,
)
from lib.jira_service_management.resources.teams import filter_teams, match_team
from lib.jira_service_management.resources.users import filter_users


def migrate() -> None:
    client = JiraServiceManagementAPIClient()

    if MIGRATE_USERS:
        print("▶ Fetching users...")
        users = client.list_users()
        if not users:
            print("No users found for migration, check configurations...")
            return
        users = filter_users(users)
    else:
        print("▶ Skipping user migration as MIGRATE_USERS is false...")
        users = []

    oncall_users = OnCallAPIClient.list_users_with_notification_rules()

    print("▶ Fetching schedules...")
    schedules = client.list_schedules()
    schedules = filter_schedules(schedules)
    oncall_schedules = OnCallAPIClient.list_all("schedules")

    print("▶ Fetching escalation policies...")
    escalation_policies = client.list_escalation_policies()
    escalation_policies = filter_escalation_policies(escalation_policies)
    oncall_escalation_chains = OnCallAPIClient.list_all("escalation_chains")

    print("▶ Fetching integrations...")
    integrations = client.list_integrations()
    integrations = filter_integrations(integrations)
    oncall_integrations = OnCallAPIClient.list_all("integrations")

    if ASSOCIATE_TEAMS:
        grafana_client = SvcGrafanaAPIClient(GRAFANA_URL, GRAFANA_SERVICE_ACCOUNT_TOKEN)
        print("▶ Fetching teams...")
        teams = client.list_teams_with_escalations()
        teams = filter_teams(teams, schedules, integrations)
        # These are oddly distinct from grafana teams, even though they are unified in the web UI
        # They also cannot be created directly, and map 1 to 1 with grafana teams
        oncall_teams = OnCallAPIClient.list_all("teams")
    else:
        teams = []
        oncall_teams = []
        grafana_client = None

    # Match users with their Grafana OnCall counterparts
    if MIGRATE_USERS:
        print("\n▶ Matching users...")
        for user in users:
            match_user(user, oncall_users)
        print(user_report(users))

    # Match teams with their Grafana OnCall counterparts
    if ASSOCIATE_TEAMS:
        print("\n▶ Matching teams...")
        for team in teams:
             match_team(team, oncall_teams)
        print(team_report(teams))

    # Match schedules with their Grafana OnCall counterparts
    print("\n▶ Matching schedules...")
    user_id_map = {
        u["id"]: u["oncall_user"]["id"] for u in users if u.get("oncall_user")
    }
    team_id_map = {t["teamId"]: t["oncall_team"]["id"] for t in teams if t.get("oncall_team")}
    print(team_id_map)
    for schedule in schedules:
        match_schedule(schedule, oncall_schedules, user_id_map, team_id_map)
        match_users_for_schedule(schedule, users)
    print(schedule_report(schedules))

    # Match escalation policies with their Grafana OnCall counterparts
    print("\n▶ Matching escalation policies...")
    for policy in escalation_policies:
        match_escalation_policy(policy, oncall_escalation_chains)
        match_users_and_schedules_for_escalation_policy(policy, users, schedules)
    print(escalation_policy_report(escalation_policies))


    # Match integrations with their Grafana OnCall counterparts
    print("\n▶ Matching integrations...")
    for integration in integrations:
        match_integration(integration, oncall_integrations, team_id_map)
    print(integration_report(integrations))


    if MODE == MODE_PLAN:
        return
        
    if ASSOCIATE_TEAMS:
        # Migrate users to teams
        print("\n▶ Creating teams and migrating users to them...")
        for team in teams:
            print(f"{TAB}Migrating {format_team(team)}...")
            team_id = grafana_client.idemopotently_create_team_and_add_users(team["displayName"], [user["email"] for user in users if user.get("oncall_user")])
            team["oncall_team"]["id"] = team_id

    # Migrate schedules
    print("\n▶ Migrating schedules...")
    for schedule in schedules:
        if not schedule.get("migration_errors"):
            print(f"{TAB}Migrating {format_schedule(schedule)}...")
            migrate_schedule(schedule, user_id_map, team_id_map)

    # Migrate escalation policies
    print("\n▶ Migrating escalation policies...")
    for policy in escalation_policies:
        if all(rule["notifyType"] != "default" for rule in policy["rules"]):
            print(
                f"{TAB}Skipping migrating {format_escalation_policy(policy)} because all of its rules "
                "have a non-default notifyType"
            )
            continue
        elif any(rule["notifyType"] != "default" for rule in policy["rules"]):
            print(
                f"{TAB}Migrating {format_escalation_policy(policy)} but some of its rules "
                "have a non-default notifyType, and those rules will not be migrated"
            )
        else:
            print(f"{TAB}Migrating {format_escalation_policy(policy)}...")

        migrate_escalation_policy(policy, users, schedules, team_id_map)

    # Migrate integrations
    print("\n▶ Migrating integrations...")
    for integration in integrations:
        print(f"{TAB}Migrating {format_integration(integration)}...")

        if (
            integration["oncall_type"] is None
            and not UNSUPPORTED_INTEGRATION_TO_WEBHOOKS
        ):
            print(
                f"{TAB}Skipping {format_integration(integration)} because it is not supported and UNSUPPORTED_INTEGRATION_TO_WEBHOOKS is false"
            )
            continue
        elif integration["oncall_type"] is None and UNSUPPORTED_INTEGRATION_TO_WEBHOOKS:
            print(
                f"{TAB}Migrating {format_integration(integration)} as webhook because it is not supported and UNSUPPORTED_INTEGRATION_TO_WEBHOOKS is true"
            )
            continue

        migrate_integration(integration)
    
