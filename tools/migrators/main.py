from lib.base_config import MIGRATING_FROM, OPSGENIE, PAGERDUTY, SPLUNK, JIRA_SERVICE_MANAGEMENT

if __name__ == "__main__":
    if MIGRATING_FROM == PAGERDUTY:
        from lib.pagerduty.migrate import migrate

        migrate()
    elif MIGRATING_FROM == SPLUNK:
        from lib.splunk.migrate import migrate

        migrate()
    elif MIGRATING_FROM == OPSGENIE:
        from lib.opsgenie.migrate import migrate

        migrate()
    elif MIGRATING_FROM == JIRA_SERVICE_MANAGEMENT:
        from lib.jira_service_management.migrate import migrate

        migrate()
    else:
        raise ValueError("Invalid MIGRATING_FROM value")
