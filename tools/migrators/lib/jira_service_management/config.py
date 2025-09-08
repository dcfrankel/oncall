import os

from lib.base_config import *  # noqa: F401,F403

DEBUG=False
JIRA_SERVICE_MANAGEMENT_API_KEY = os.environ["JIRA_SERVICE_MANAGEMENT_API_KEY"]
JIRA_SERVICE_MANAGEMENT_BASE_API_URL = os.getenv(
    "JIRA_SERVICE_MANAGEMENT_BASE_API_URL", "https://api.atlassian.com"
)
JIRA_SERVICE_MANAGEMENT_INSTANCE_API_URL = os.environ["JIRA_SERVICE_MANAGEMENT_INSTANCE_API_URL"]
JIRA_SERVICE_MANAGEMENT_CLOUD_ID = os.environ["JIRA_SERVICE_MANAGEMENT_CLOUD_ID"]
JIRA_SERVICE_MANAGEMENT_ORG_ID = os.environ["JIRA_SERVICE_MANAGEMENT_ORG_ID"]
JIRA_SERVICE_MANAGEMENT_TO_ONCALL_CONTACT_METHOD_MAP = {
    "sms": "notify_by_sms",
    "voice": "notify_by_phone_call",
    "email": "notify_by_email",
    "mobile": "notify_by_mobile_app",
}

JIRA_SERVICE_MANAGEMENT_TO_ONCALL_VENDOR_MAP = {
    "Amazon CloudWatch": "amazon_sns",
    "AmazonSns": "amazon_sns",
    "AppDynamics": "appdynamics",
    "CloudWatch": "amazon_sns",
    "CloudWatchEvents": "amazon_sns",
    "Datadog": "datadog",
    "Email": "inbound_email",
    "Jira": "jira",
    "JiraServiceDesk": "jira",
    "Kapacitor": "kapacitor",
    "NewRelic": "newrelic",
    "NewRelicV2": "newrelic",
    "PingdomV2": "pingdom",
    "Prometheus": "alertmanager",
    "Prtg": "prtg",
    "Scout": "webhook",
    "Sentry": "sentry",
    "Stackdriver": "stackdriver",
    "UptimeRobot": "uptimerobot",
    "Webhook": "webhook",
    "Zabbix": "zabbix",
    "Honeycomb": "formatted_webhook",
}

# Set to true to migrate unsupported integrations to OnCall webhook integration
UNSUPPORTED_INTEGRATION_TO_WEBHOOKS = (
    os.getenv("UNSUPPORTED_INTEGRATION_TO_WEBHOOKS", "false").lower() == "true"
)

MIGRATE_USERS = os.getenv("MIGRATE_USERS", "true").lower() == "true"

# Filter resources by team
JIRA_SERVICE_MANAGEMENT_FILTER_TEAM = os.getenv("JIRA_SERVICE_MANAGEMENT_FILTER_TEAM")

# Filter resources by users (comma-separated list of Jira Service Management user IDs)
JIRA_SERVICE_MANAGEMENT_FILTER_USERS = [
    user_id.strip()
    for user_id in os.getenv("JIRA_SERVICE_MANAGEMENT_FILTER_USERS", "").split(",")
    if user_id.strip()
]

# Filter resources by name regex patterns
JIRA_SERVICE_MANAGEMENT_FILTER_SCHEDULE_REGEX = os.getenv(
    "JIRA_SERVICE_MANAGEMENT_FILTER_SCHEDULE_REGEX"
)
JIRA_SERVICE_MANAGEMENT_FILTER_ESCALATION_POLICY_REGEX = os.getenv(
    "JIRA_SERVICE_MANAGEMENT_FILTER_ESCALATION_POLICY_REGEX"
)
JIRA_SERVICE_MANAGEMENT_FILTER_INTEGRATION_REGEX = os.getenv(
    "JIRA_SERVICE_MANAGEMENT_FILTER_INTEGRATION_REGEX"
)

# Link schedules, escalation chains, etc... to specific teams
ASSOCIATE_TEAMS = os.getenv("ASSOCIATE_TEAMS", "false").lower() == "true"

# Required to work with Grafana APIs
GRAFANA_SERVICE_ACCOUNT_TOKEN = os.getenv("GRAFANA_SERVICE_ACCOUNT_TOKEN")
GRAFANA_URL = os.getenv("GRAFANA_URL")
