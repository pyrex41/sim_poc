#!/usr/bin/env python3
"""
Test script for Clients and Campaigns API endpoints.

This script tests all CRUD operations and validates the API responses.
"""

import requests
import json
import sys
from typing import Optional

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


class APITester:
    """API endpoint tester."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.token: Optional[str] = None
        self.client_id: Optional[str] = None
        self.campaign_id: Optional[str] = None
        self.tests_passed = 0
        self.tests_failed = 0

    def print_success(self, message: str):
        """Print success message."""
        print(f"{Colors.GREEN}✓ {message}{Colors.END}")
        self.tests_passed += 1

    def print_error(self, message: str):
        """Print error message."""
        print(f"{Colors.RED}✗ {message}{Colors.END}")
        self.tests_failed += 1

    def print_info(self, message: str):
        """Print info message."""
        print(f"{Colors.BLUE}ℹ {message}{Colors.END}")

    def print_warning(self, message: str):
        """Print warning message."""
        print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

    def get_headers(self) -> dict:
        """Get request headers with auth token."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def login(self, username: str = "testuser", password: str = "testpass") -> bool:
        """Authenticate and get token."""
        self.print_info(f"Attempting login for user: {username}")
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                data={"username": username, "password": password},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.print_success(f"Login successful (token: {self.token[:20]}...)")
                return True
            else:
                self.print_error(f"Login failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Login exception: {e}")
            return False

    def test_create_client(self) -> bool:
        """Test POST /api/clients"""
        self.print_info("Testing: POST /api/clients")

        payload = {
            "name": "Test Client Corp",
            "description": "A test client for API testing",
            "brandGuidelines": {
                "colors": ["#FF0000", "#0000FF", "#00FF00"],
                "fonts": ["Helvetica Neue", "Arial"],
                "styleKeywords": ["modern", "minimalist", "professional"],
                "documentUrls": ["https://example.com/brand-guide.pdf"]
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/clients",
                json=payload,
                headers=self.get_headers()
            )

            if response.status_code == 201:
                data = response.json()
                if "data" in data and "id" in data["data"]:
                    self.client_id = data["data"]["id"]
                    self.print_success(f"Client created successfully (ID: {self.client_id})")
                    return True
                else:
                    self.print_error(f"Unexpected response format: {data}")
                    return False
            else:
                self.print_error(f"Failed to create client: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Exception during client creation: {e}")
            return False

    def test_get_clients(self) -> bool:
        """Test GET /api/clients"""
        self.print_info("Testing: GET /api/clients")

        try:
            response = requests.get(
                f"{self.base_url}/clients",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                data = response.json()
                if "data" in data and isinstance(data["data"], list):
                    self.print_success(f"Retrieved {len(data['data'])} clients")
                    return True
                else:
                    self.print_error(f"Unexpected response format: {data}")
                    return False
            else:
                self.print_error(f"Failed to get clients: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Exception during get clients: {e}")
            return False

    def test_get_client_by_id(self) -> bool:
        """Test GET /api/clients/:id"""
        if not self.client_id:
            self.print_warning("Skipping: No client ID available")
            return True

        self.print_info(f"Testing: GET /api/clients/{self.client_id}")

        try:
            response = requests.get(
                f"{self.base_url}/clients/{self.client_id}",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                data = response.json()
                if "data" in data and data["data"]["id"] == self.client_id:
                    self.print_success(f"Retrieved client: {data['data']['name']}")
                    return True
                else:
                    self.print_error(f"Unexpected response: {data}")
                    return False
            else:
                self.print_error(f"Failed to get client: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Exception during get client: {e}")
            return False

    def test_update_client(self) -> bool:
        """Test PATCH /api/clients/:id"""
        if not self.client_id:
            self.print_warning("Skipping: No client ID available")
            return True

        self.print_info(f"Testing: PATCH /api/clients/{self.client_id}")

        payload = {
            "description": "Updated description for testing"
        }

        try:
            response = requests.patch(
                f"{self.base_url}/clients/{self.client_id}",
                json=payload,
                headers=self.get_headers()
            )

            if response.status_code == 200:
                data = response.json()
                if "data" in data and data["data"]["description"] == payload["description"]:
                    self.print_success("Client updated successfully")
                    return True
                else:
                    self.print_error(f"Update not reflected: {data}")
                    return False
            else:
                self.print_error(f"Failed to update client: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Exception during update client: {e}")
            return False

    def test_get_client_stats(self) -> bool:
        """Test GET /api/clients/:id/stats"""
        if not self.client_id:
            self.print_warning("Skipping: No client ID available")
            return True

        self.print_info(f"Testing: GET /api/clients/{self.client_id}/stats")

        try:
            response = requests.get(
                f"{self.base_url}/clients/{self.client_id}/stats",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                data = response.json()
                if "data" in data and "campaignCount" in data["data"]:
                    stats = data["data"]
                    self.print_success(
                        f"Client stats: {stats['campaignCount']} campaigns, "
                        f"{stats['videoCount']} videos, ${stats['totalSpend']} spent"
                    )
                    return True
                else:
                    self.print_error(f"Unexpected stats format: {data}")
                    return False
            else:
                self.print_error(f"Failed to get stats: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Exception during get stats: {e}")
            return False

    def test_create_campaign(self) -> bool:
        """Test POST /api/campaigns"""
        if not self.client_id:
            self.print_warning("Skipping: No client ID available")
            return True

        self.print_info("Testing: POST /api/campaigns")

        payload = {
            "clientId": self.client_id,
            "name": "Test Campaign 2024",
            "goal": "Test goal: Increase brand awareness by 50%",
            "status": "active",
            "brief": {
                "objective": "Drive awareness and engagement",
                "targetAudience": "Tech professionals 25-45",
                "keyMessages": ["Innovation", "Quality", "Performance"]
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/campaigns",
                json=payload,
                headers=self.get_headers()
            )

            if response.status_code == 201:
                data = response.json()
                if "data" in data and "id" in data["data"]:
                    self.campaign_id = data["data"]["id"]
                    self.print_success(f"Campaign created successfully (ID: {self.campaign_id})")
                    return True
                else:
                    self.print_error(f"Unexpected response format: {data}")
                    return False
            else:
                self.print_error(f"Failed to create campaign: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Exception during campaign creation: {e}")
            return False

    def test_get_campaigns(self) -> bool:
        """Test GET /api/campaigns"""
        self.print_info("Testing: GET /api/campaigns")

        try:
            response = requests.get(
                f"{self.base_url}/campaigns",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                data = response.json()
                if "data" in data and isinstance(data["data"], list):
                    self.print_success(f"Retrieved {len(data['data'])} campaigns")
                    return True
                else:
                    self.print_error(f"Unexpected response format: {data}")
                    return False
            else:
                self.print_error(f"Failed to get campaigns: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Exception during get campaigns: {e}")
            return False

    def test_get_campaigns_by_client(self) -> bool:
        """Test GET /api/campaigns?clientId=:id"""
        if not self.client_id:
            self.print_warning("Skipping: No client ID available")
            return True

        self.print_info(f"Testing: GET /api/campaigns?clientId={self.client_id}")

        try:
            response = requests.get(
                f"{self.base_url}/campaigns?clientId={self.client_id}",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                data = response.json()
                if "data" in data and isinstance(data["data"], list):
                    # All campaigns should belong to the client
                    for campaign in data["data"]:
                        if campaign.get("clientId") != self.client_id:
                            self.print_error(f"Campaign {campaign['id']} doesn't belong to client")
                            return False
                    self.print_success(f"Retrieved {len(data['data'])} campaigns for client")
                    return True
                else:
                    self.print_error(f"Unexpected response format: {data}")
                    return False
            else:
                self.print_error(f"Failed to get campaigns: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Exception during get campaigns by client: {e}")
            return False

    def test_get_campaign_by_id(self) -> bool:
        """Test GET /api/campaigns/:id"""
        if not self.campaign_id:
            self.print_warning("Skipping: No campaign ID available")
            return True

        self.print_info(f"Testing: GET /api/campaigns/{self.campaign_id}")

        try:
            response = requests.get(
                f"{self.base_url}/campaigns/{self.campaign_id}",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                data = response.json()
                if "data" in data and data["data"]["id"] == self.campaign_id:
                    self.print_success(f"Retrieved campaign: {data['data']['name']}")
                    return True
                else:
                    self.print_error(f"Unexpected response: {data}")
                    return False
            else:
                self.print_error(f"Failed to get campaign: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Exception during get campaign: {e}")
            return False

    def test_update_campaign(self) -> bool:
        """Test PATCH /api/campaigns/:id"""
        if not self.campaign_id:
            self.print_warning("Skipping: No campaign ID available")
            return True

        self.print_info(f"Testing: PATCH /api/campaigns/{self.campaign_id}")

        payload = {
            "status": "archived"
        }

        try:
            response = requests.patch(
                f"{self.base_url}/campaigns/{self.campaign_id}",
                json=payload,
                headers=self.get_headers()
            )

            if response.status_code == 200:
                data = response.json()
                if "data" in data and data["data"]["status"] == payload["status"]:
                    self.print_success("Campaign updated successfully")
                    return True
                else:
                    self.print_error(f"Update not reflected: {data}")
                    return False
            else:
                self.print_error(f"Failed to update campaign: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Exception during update campaign: {e}")
            return False

    def test_get_campaign_stats(self) -> bool:
        """Test GET /api/campaigns/:id/stats"""
        if not self.campaign_id:
            self.print_warning("Skipping: No campaign ID available")
            return True

        self.print_info(f"Testing: GET /api/campaigns/{self.campaign_id}/stats")

        try:
            response = requests.get(
                f"{self.base_url}/campaigns/{self.campaign_id}/stats",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                data = response.json()
                if "data" in data and "videoCount" in data["data"]:
                    stats = data["data"]
                    self.print_success(
                        f"Campaign stats: {stats['videoCount']} videos, "
                        f"${stats['totalSpend']} spent, ${stats['avgCost']} avg"
                    )
                    return True
                else:
                    self.print_error(f"Unexpected stats format: {data}")
                    return False
            else:
                self.print_error(f"Failed to get stats: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Exception during get stats: {e}")
            return False

    def test_delete_campaign(self) -> bool:
        """Test DELETE /api/campaigns/:id"""
        if not self.campaign_id:
            self.print_warning("Skipping: No campaign ID available")
            return True

        self.print_info(f"Testing: DELETE /api/campaigns/{self.campaign_id}")

        try:
            response = requests.delete(
                f"{self.base_url}/campaigns/{self.campaign_id}",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                self.print_success("Campaign deleted successfully")
                self.campaign_id = None
                return True
            else:
                self.print_error(f"Failed to delete campaign: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Exception during delete campaign: {e}")
            return False

    def test_delete_client(self) -> bool:
        """Test DELETE /api/clients/:id"""
        if not self.client_id:
            self.print_warning("Skipping: No client ID available")
            return True

        self.print_info(f"Testing: DELETE /api/clients/{self.client_id}")

        try:
            response = requests.delete(
                f"{self.base_url}/clients/{self.client_id}",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                self.print_success("Client deleted successfully")
                self.client_id = None
                return True
            else:
                self.print_error(f"Failed to delete client: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Exception during delete client: {e}")
            return False

    def run_all_tests(self):
        """Run all test cases."""
        print("\n" + "=" * 70)
        print("Testing Clients and Campaigns API Endpoints")
        print("=" * 70 + "\n")

        # Authentication
        if not self.login():
            self.print_error("Authentication failed. Cannot proceed with tests.")
            return False

        print("\n--- Client Tests ---\n")
        self.test_create_client()
        self.test_get_clients()
        self.test_get_client_by_id()
        self.test_update_client()
        self.test_get_client_stats()

        print("\n--- Campaign Tests ---\n")
        self.test_create_campaign()
        self.test_get_campaigns()
        self.test_get_campaigns_by_client()
        self.test_get_campaign_by_id()
        self.test_update_campaign()
        self.test_get_campaign_stats()

        print("\n--- Cleanup Tests ---\n")
        self.test_delete_campaign()
        self.test_delete_client()

        # Summary
        print("\n" + "=" * 70)
        print("Test Summary")
        print("=" * 70)
        print(f"{Colors.GREEN}Passed: {self.tests_passed}{Colors.END}")
        print(f"{Colors.RED}Failed: {self.tests_failed}{Colors.END}")
        print(f"Total: {self.tests_passed + self.tests_failed}")

        if self.tests_failed == 0:
            print(f"\n{Colors.GREEN}All tests passed! ✓{Colors.END}\n")
            return True
        else:
            print(f"\n{Colors.RED}Some tests failed. ✗{Colors.END}\n")
            return False


def main():
    """Main entry point."""
    tester = APITester(API_BASE)
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
