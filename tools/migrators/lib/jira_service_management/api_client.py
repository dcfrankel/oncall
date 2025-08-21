import typing
from urllib.parse import parse_qs, urlparse

from requests.exceptions import HTTPError

from lib.network import api_call
from lib.jira_service_management.config import (
    JIRA_SERVICE_MANAGEMENT_API_KEY,
    JIRA_SERVICE_MANAGEMENT_BASE_API_URL,
    JIRA_SERVICE_MANAGEMENT_INSTANCE_API_URL,
    JIRA_SERVICE_MANAGEMENT_CLOUD_ID,
    JIRA_SERVICE_MANAGEMENT_ORG_ID,
)

class JiraServiceManagementAPIClient:
    DEFAULT_LIMIT = 100


    def __init__(
        self, 
        api_key: str = JIRA_SERVICE_MANAGEMENT_API_KEY,
        base_api_url: str = JIRA_SERVICE_MANAGEMENT_BASE_API_URL, 
        instance_api_url: str = JIRA_SERVICE_MANAGEMENT_INSTANCE_API_URL, 
        cloud_id: str = JIRA_SERVICE_MANAGEMENT_CLOUD_ID,
        org_id: str = JIRA_SERVICE_MANAGEMENT_ORG_ID,
    ):
        self.api_key = api_key
        self.base_api_url = base_api_url
        self.instance_api_url = instance_api_url
        self.cloud_id = cloud_id
        self.org_id = org_id
        self.headers = {
            "Authorization": f"Basic {self.api_key}",
            "Content-Type": "application/json",
        }

    def _make_request(
        self,
        method: str,
        path: str,
        params: typing.Optional[dict] = None,
        json: typing.Optional[dict] = None,
        paginate: bool = True,
    ) -> dict:
        """
        Make a request to the Jira Service Management API with automatic pagination handling.
        If paginate=True and method is GET, it will automatically handle pagination
        and combine all results into a single response.
        """
        if params is None:
            params = {}

        # Only handle pagination for GET requests when pagination is requested
        if method.upper() != "GET" or not paginate:
            response = api_call(
                method,
                self.base_api_url,
                path,
                headers=self.headers,
                params=params,
                json=json,
            )
            return response.json()

        # Set default pagination parameters
        if "limit" not in params:
            params["limit"] = self.DEFAULT_LIMIT
        if "offset" not in params:
            params["offset"] = 0

        # Initialize combined response
        combined_response = None

        while True:
            response = api_call(
                method,
                self.base_api_url,
                path,
                headers=self.headers,
                params=params,
                json=json,
            )
            response_json = response.json()

            if combined_response is None:
                combined_response = response_json
            else:
                # Extend the data array with new items
                combined_response["values"].extend(response_json.get("values", []))

            # Check if there's more data to fetch
            data = response_json.get("values", [])
            if not data:
                break

            # Check if there's a next page in the paging information
            paging = response_json.get("paging", {})
            next_url = paging.get("next")
            if not next_url:
                break

            # Parse the next URL to get the new offset
            parsed_url = urlparse(next_url)
            query_params = parse_qs(parsed_url.query)

            try:
                params["offset"] = int(query_params.get("offset", [0])[0])
            except (ValueError, IndexError):
                break

        return combined_response

    def _make_team_request(
        self,
        method: str,
        path: str,
        params: typing.Optional[dict] = None,
        json: typing.Optional[dict] = None,
        paginate: bool = True,
    ) -> dict:
        """
        Make a request to the Jira Service Management API with automatic pagination handling.
        If paginate=True and method is GET, it will automatically handle pagination
        and combine all results into a single response.
        """
        if params is None:
            params = {}

        # Only handle pagination for GET requests when pagination is requested
        if method.upper() != "GET" or not paginate:
            response = api_call(
                method,
                self.base_api_url,
                path,
                headers=self.headers,
                params=params,
                json=json,
            )
            return response.json()

        # Set default pagination parameters
        if "size" not in params:
            params["size"] = self.DEFAULT_LIMIT

        # Initialize combined response
        combined_response = []
        cursor = None

        while True:
            # Use a cursor if it's been set
            if cursor:
                params["cursor"] = cursor

            response = api_call(
                method,
                self.base_api_url,
                path,
                headers=self.headers,
                params=params,
                json=json,
            )
            response_json = response.json()

            # Check if there's more data to fetch
            data = response_json.get("entities", [])
            if not response_json or not data:
                break

            # Extend the data array with new items
            combined_response["entities"].extend(response_json.get("entities", []))

            # Check if there's a next page in the paging information
            cursor = response_json.get("cursor", "")

            if not cursor:
                break

        return combined_response.get("entities", [])

    def _make_user_request(
        self,
        method: str,
        path: str,
        params: typing.Optional[dict] = None,
        json: typing.Optional[dict] = None,
        paginate: bool = True,
    ) -> dict:
        """
        Make a request to the Jira Service Management API with automatic pagination handling.
        If paginate=True and method is GET, it will automatically handle pagination
        and combine all results into a single response.
        """
        if params is None:
            params = {}

        # Only handle pagination for GET requests when pagination is requested
        if method.upper() != "GET" or not paginate:
            response = api_call(
                method,
                self.instance_api_url,
                path,
                headers=self.headers,
                params=params,
                json=json,
            )
            return response.json()

        # Set default pagination parameters
        if "startAt" not in params:
            params["startAt"] = 0
        if "maxResults" not in params:
            params["maxResults"] = self.DEFAULT_LIMIT

        # Initialize combined response
        combined_response = []

        while True:
            response = api_call(
                method,
                self.instance_api_url,
                path,
                headers=self.headers,
                params=params,
                json=json,
            )

            # Increment startAt by maxResults to move position
            params["startAt"] += params["maxResults"]
            response_json = response.json()

            # Check if there's more data to fetch
            if not response_json:
                break

            # Extend the data array with new items
            combined_response.extend(response_json)


        return combined_response

    def list_users(self) -> list[dict]:
        """
        List all users and their teams.
        Note: User notifications are not supported due to limitations of the JSM API. The API requires basic
        authentication, and only notifications for the current user are returned.
        """
        users = []
        response = self._make_user_request("GET", "rest/api/3/users")

        teams_cache = {}
        for user in response.get("data", []):
            # Skip inactive users and non regular users
            if not user.get("active") or user.get("accountId") == "atlassian":
                continue

            # Map username to email for compatibility with matching function
            user["email"] = user["emailAddress"]
            user["id"] = user["accountId"]

            user_account_id = user["accountId"]
            user["teams"] = []
            if not teams_cache:
                # Get teams for user if not cached
                teams_response = self.list_teams()
                for team in teams_response.get("entities", []):
                    team_id = team["teamId"]
                    # Expected for matching function
                    team["id"] = team_id
                    teams_cache[team_id] = team
                
                    # Get team members since this doesn't exist on the base team response
                    teams_members_response = self._make_request("GET", f"public/teams/v1/org/{self.org_id}/teams/{team_id}/members")
                    members = [member["accountId"] for member in teams_members_response.get("results", [])]
                    if user_account_id in members:
                        user["teams"].append(team)
                    teams_cache[team_id]["members"] = members
            else:
                # Use cached teams
                for team_id, team in teams_cache.items():
                    if user_account_id in team["members"]:
                        user["teams"].append(team)

            users.append(user)

        return users

    def list_schedules(self) -> list[dict]:
        """List all schedules with their rotations."""
        response = self._make_request(
            "GET", f"/jsm/ops/api/{self.cloud_id}/v1/schedules", params={"expand": "rotation"}
        )
        schedules = response.get("values", [])


        # Fetch overrides for each schedule
        for schedule in schedules:
            overrides_response = self._make_request(
                "GET", f"/jsm/ops/api/{self.cloud_id}/v1/schedules/{schedule['id']}/overrides"
            )
            schedule["overrides"] = overrides_response.get("values", [])

            # Clean up deleted users
            for rotation in schedule["rotations"]:
                rotation["participants"] = [p for p in rotation["participants"] if p["type"] == "user" and "deleted" not in p]

        return schedules

    def list_escalation_policies(self) -> list[dict]:
        """List all escalation policies."""
        response = self.list_teams()
        escalations = []

        # Get escalations for each team
        for team in response:
            try:
                team_escalations = self._make_request(
                    "GET", f"/jsm/ops/api/{self.cloud_id}/v1/teams/{team['teamId']}/escalations"
                )
            except HTTPError as e:
                if e.response.status_code == 404:
                    print(f"Team {team['displayName']} - {team['teamId']} not found or has no escalations, skipping...")
                    continue
                else:
                    raise
            team_escalations = team_escalations.get("values", [])
            for escalation in team_escalations:
                # Add the expected fields to each rule
                escalation["ownerTeam"] = {
                    "id": team["teamId"],
                    "name": team["displayName"],
                }
            escalations.extend(team_escalations)

        return escalations

    def list_teams(self) -> list[dict]:
        """List all teams."""
        response = self._make_team_request("GET", f"public/teams/v1/org/{self.org_id}/teams")
        return response

    def list_integrations(self) -> list[dict]:
        """List all integrations."""
        response = self._make_request("GET", f"jsm/ops/api/{self.cloud_id}/v1/integrations")
        return response.get("values", [])

    def list_services(self) -> list[dict]:
        """List all services."""
        raise NotImplementedError("Not implemented")

