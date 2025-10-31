"""
Load testing for WindexAI using Locust
"""
from locust import HttpUser, task, between
from faker import Faker
import json


class WindexAIUser(HttpUser):
    """Simulated user for load testing"""

    wait_time = between(1, 3)
    fake = Faker()

    def on_start(self):
        """Setup user session"""
        self.register_and_login()

    def register_and_login(self):
        """Register a new user and login"""
        # Generate random user data
        username = f"user_{self.fake.user_name()}_{self.user_id}"
        email = f"{username}@test.com"
        password = "testpassword123"

        # Register user
        register_data = {
            "username": username,
            "email": email,
            "password": password
        }

        register_response = self.client.post("/api/auth/register", json=register_data)

        # If user already exists (due to username collision), try login
        if register_response.status_code == 400:
            login_data = {
                "username": username,
                "password": password
            }
            login_response = self.client.post("/api/auth/login", data=login_data)
        else:
            # Login with newly created user
            login_data = {
                "username": username,
                "password": password
            }
            login_response = self.client.post("/api/auth/login", data=login_data)

        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {token}"}
        else:
            # Fallback - use a test user if registration/login fails
            self.headers = {}

    @task(1)
    def get_models(self):
        """Get available models"""
        self.client.get("/api/models")

    @task(3)
    def chat_interaction(self):
        """Simulate chat interaction"""
        messages = [
            "Привет! Расскажи о себе",
            "Что ты умеешь делать?",
            "Как работает искусственный интеллект?",
            "Расскажи о Python",
            "Что такое машинное обучение?",
            "Объясни как создать веб-сайт",
            "Какие есть фреймворки для Python?",
            "Что такое API?",
            "Как оптимизировать производительность?",
            "Расскажи о базах данных"
        ]

        message = self.fake.random_element(messages)

        chat_data = {
            "message": message,
            "model": "gpt-4o-mini"
        }

        # Skip actual chat if no auth headers (failed login)
        if self.headers:
            response = self.client.post("/api/chat/", json=chat_data, headers=self.headers)
            if response.status_code == 200:
                # Store conversation ID for follow-up messages
                data = response.json()
                self.conversation_id = data.get("conversation_id")

    @task(2)
    def get_conversations(self):
        """Get user's conversations"""
        if hasattr(self, 'headers') and self.headers:
            self.client.get("/api/chat/conversations", headers=self.headers)

    @task(1)
    def health_check(self):
        """Health check"""
        self.client.get("/health")

    @task(1)
    def get_profile(self):
        """Get user profile"""
        if hasattr(self, 'headers') and self.headers:
            self.client.get("/api/auth/me", headers=self.headers)


class ChatHeavyUser(WindexAIUser):
    """User focused on chat interactions"""

    @task(10)
    def chat_interaction(self):
        """Heavy chat usage"""
        super().chat_interaction()

    @task(2)
    def follow_up_chat(self):
        """Follow-up messages in conversation"""
        if hasattr(self, 'conversation_id') and hasattr(self, 'headers') and self.headers:
            messages = [
                "Расскажи подробнее",
                "Что еще?",
                "Приведи пример",
                "Как это работает?",
                "Дай больше информации"
            ]

            message = self.fake.random_element(messages)
            chat_data = {
                "message": message,
                "model": "gpt-4o-mini",
                "conversation_id": self.conversation_id
            }

            self.client.post("/api/chat/", json=chat_data, headers=self.headers)


class ReadOnlyUser(WindexAIUser):
    """User that only reads data"""

    @task(5)
    def get_models(self):
        super().get_models()

    @task(3)
    def get_conversations(self):
        if hasattr(self, 'headers') and self.headers:
            self.client.get("/api/chat/conversations", headers=self.headers)

    @task(2)
    def health_check(self):
        super().health_check()
