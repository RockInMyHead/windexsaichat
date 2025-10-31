"""
Unit tests for AuthService
"""
import pytest
from unittest.mock import MagicMock, patch

from services.auth_service import AuthService
from schemas.user import UserCreate


class TestAuthService:
    def setup_method(self):
        """Setup for each test method"""
        self.auth_service = AuthService("test-secret", "HS256")

    def test_verify_password_success(self):
        """Test successful password verification"""
        hashed = self.auth_service.get_password_hash("password123")
        assert self.auth_service.verify_password("password123", hashed)

    def test_verify_password_failure(self):
        """Test failed password verification"""
        hashed = self.auth_service.get_password_hash("password123")
        assert not self.auth_service.verify_password("wrongpassword", hashed)

    def test_get_password_hash(self):
        """Test password hashing"""
        hashed = self.auth_service.get_password_hash("testpassword")
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed != "testpassword"

    @patch('services.auth_service.jwt.encode')
    def test_create_access_token(self, mock_encode):
        """Test JWT token creation"""
        mock_encode.return_value = "test-token"
        token = self.auth_service.create_access_token({"sub": "testuser"})
        assert token == "test-token"
        mock_encode.assert_called_once()

    @patch('services.auth_service.jwt.decode')
    def test_verify_token_success(self, mock_decode):
        """Test successful token verification"""
        mock_decode.return_value = {"sub": "testuser"}
        result = self.auth_service.verify_token("valid-token")
        assert result.username == "testuser"

    @patch('services.auth_service.jwt.decode')
    def test_verify_token_failure(self, mock_decode):
        """Test failed token verification"""
        from jose import JWTError
        mock_decode.side_effect = JWTError("Invalid token")
        result = self.auth_service.verify_token("invalid-token")
        assert result is None

    def test_authenticate_user_success(self, db_session):
        """Test successful user authentication"""
        # Create test user
        user_data = UserCreate(username="testuser", email="test@example.com", password="password123")
        user = self.auth_service.create_user(db_session, user_data)

        # Authenticate
        result = self.auth_service.authenticate_user(db_session, "testuser", "password123")
        assert result is not None
        assert result.username == "testuser"

    def test_authenticate_user_wrong_password(self, db_session):
        """Test authentication with wrong password"""
        # Create test user
        user_data = UserCreate(username="testuser", email="test@example.com", password="password123")
        self.auth_service.create_user(db_session, user_data)

        # Try to authenticate with wrong password
        result = self.auth_service.authenticate_user(db_session, "testuser", "wrongpassword")
        assert result is None

    def test_authenticate_user_not_found(self, db_session):
        """Test authentication for non-existent user"""
        result = self.auth_service.authenticate_user(db_session, "nonexistent", "password123")
        assert result is None

    def test_create_user_success(self, db_session):
        """Test successful user creation"""
        user_data = UserCreate(username="newuser", email="new@example.com", password="password123")
        user = self.auth_service.create_user(db_session, user_data)

        assert user.username == "newuser"
        assert user.email == "new@example.com"
        assert user.hashed_password != "password123"  # Should be hashed

    def test_create_user_duplicate_username(self, db_session):
        """Test user creation with duplicate username"""
        user_data = UserCreate(username="duplicate", email="test1@example.com", password="password123")
        self.auth_service.create_user(db_session, user_data)

        # Try to create another user with same username
        duplicate_data = UserCreate(username="duplicate", email="test2@example.com", password="password456")
        with pytest.raises(Exception):  # Should raise IntegrityError
            self.auth_service.create_user(db_session, duplicate_data)

    def test_get_user_by_username_found(self, db_session):
        """Test getting user by username when exists"""
        user_data = UserCreate(username="findme", email="findme@example.com", password="password123")
        created_user = self.auth_service.create_user(db_session, user_data)

        found_user = self.auth_service.get_user_by_username(db_session, "findme")
        assert found_user is not None
        assert found_user.username == "findme"

    def test_get_user_by_username_not_found(self, db_session):
        """Test getting user by username when doesn't exist"""
        found_user = self.auth_service.get_user_by_username(db_session, "nonexistent")
        assert found_user is None
