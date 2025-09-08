import re
from typing import List

from lib.oncall.api_client import OnCallAPIClient
from lib.jira_service_management.config import (
    ASSOCIATE_TEAMS,
    JIRA_SERVICE_MANAGEMENT_FILTER_INTEGRATION_REGEX,
    JIRA_SERVICE_MANAGEMENT_FILTER_TEAM,
    JIRA_SERVICE_MANAGEMENT_TO_ONCALL_VENDOR_MAP,
    UNSUPPORTED_INTEGRATION_TO_WEBHOOKS,
)


def filter_integrations(integrations: list[dict]) -> list[dict]:
    """Apply filters to integrations."""
    if JIRA_SERVICE_MANAGEMENT_FILTER_TEAM:
        integrations = [
            i for i in integrations if i.get("teamId") == JIRA_SERVICE_MANAGEMENT_FILTER_TEAM
        ]

    if JIRA_SERVICE_MANAGEMENT_FILTER_INTEGRATION_REGEX:
        pattern = re.compile(JIRA_SERVICE_MANAGEMENT_FILTER_INTEGRATION_REGEX)
        integrations = [i for i in integrations if pattern.match(i["name"])]

    return integrations


def match_integration(integration: dict, oncall_integrations: List[dict], team_id_map: dict[str, str]) -> None:
    """
    Match Jira Service Management integration with Grafana OnCall integration + match jira service management
    integration type with Grafana OnCall integration type.
    """
    oncall_integration = None
    for candidate in oncall_integrations:
        name = integration["name"].lower().strip()
        if name == candidate["name"].lower().strip():
            oncall_integration = candidate

    integration["oncall_integration"] = oncall_integration

    integration_type = JIRA_SERVICE_MANAGEMENT_TO_ONCALL_VENDOR_MAP.get(integration["type"])
    if not integration_type and UNSUPPORTED_INTEGRATION_TO_WEBHOOKS:
        integration_type = "webhook"
    integration["oncall_type"] = integration_type
    integration["team_id"] = team_id_map.get(integration["teamId"])


def migrate_integration_and_routes(integration: dict) -> None:
    """Migrate Jira Service Management integration to Grafana OnCall."""
    if integration["oncall_integration"]:
        OnCallAPIClient.delete(
            f"integrations/{integration['oncall_integration']['id']}"
        )

    # Create new integration
    payload = {
        "name": integration["name"],
        "type": integration["oncall_type"],
        "team_id": None,
    }

    if ASSOCIATE_TEAMS:
        payload["team_id"] = integration.get("team_id")

    escalation_chain_id = integration.get("oncall_escalation_chain", {}).get("id")
    payload["escalation_chain_id"] = escalation_chain_id
 
    integration["oncall_integration"] = OnCallAPIClient.create("integrations", payload)

    if integration["oncall_type"] == "alertmanager":
        # Delete existing routes
        routes = OnCallAPIClient.list_all(
            f"routes/?integration_id={integration['oncall_integration']['id']}"
        )
        for route in routes:
            if route["is_the_last_route"]:
                # Can't delete the default route
                continue
            OnCallAPIClient.delete(f"routes/{route['id']}")

        # Create standard routes for alertmanager integrations
        route = { 
                "integration_id": integration["oncall_integration"]["id"],
                "routing_type": "jinja2",
                "escalation_chain_id": escalation_chain_id,
                "routing_regex": "{% set groupLabels = payload.get(\"groupLabels\", {}) -%}\n{% set severity = groupLabels.severity -%}\n{{ severity == \"critical\" }}",
                "position": 0,
                "is_the_last_route": False
        }

        OnCallAPIClient.create("routes", route)
