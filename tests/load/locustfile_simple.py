"""
Simple load testing for WindexAI without AI calls
"""
from locust import HttpUser, task, between
from faker import Faker


class SimpleWindexAIUser(HttpUser):
    """Simple user for load testing without expensive AI calls"""

    wait_time = between(1, 3)
    fake = Faker()

    @task(5)
    def health_check(self):
        """Health check - lightweight endpoint"""
        response = self.client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    @task(3)
    def get_models(self):
        """Get available models"""
        response = self.client.get("/api/models")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert "gpt-4o-mini" in data["models"]

    @task(2)
    def invalid_auth(self):
        """Test authentication failure - should be fast"""
        response = self.client.get("/api/auth/me")
        # In our API, unauthenticated requests return 403, not 401
        assert response.status_code in [401, 403]

    @task(1)
    def register_user(self):
        """Register new user - tests database writes"""
        # Generate unique username without user_id
        username = f"user_{self.fake.user_name()}_{self.fake.random_int(1000, 9999)}"
        email = f"{username}@test.com"

        user_data = {
            "username": username,
            "email": email,
            "password": "testpassword123"
        }

        response = self.client.post("/api/auth/register", json=user_data)
        # Accept both success (201) and conflict (400) for duplicate users
        assert response.status_code in [200, 400]

    @task(1)
    def get_root_page(self):
        """Get root HTML page"""
        response = self.client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
