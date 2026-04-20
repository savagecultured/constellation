"""Tests for security module."""
import pytest
from app.core.security import verify_password, get_password_hash, create_access_token, decode_token
from app.core.config import settings


class TestPasswordHashing:
    """Test password hashing functions."""
    
    def test_get_password_hash(self):
        """Test that password hashing works."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_verify_password_empty(self):
        """Test password verification with empty password."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert verify_password("", hashed) is False


class TestTokenGeneration:
    """Test JWT token generation and decoding."""
    
    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_decode_token(self):
        """Test token decoding."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        payload = decode_token(token)
        
        assert payload is not None
        assert payload.get("sub") == "testuser"
        assert payload.get("type") == "access"
    
    def test_decode_invalid_token(self):
        """Test decoding invalid token."""
        payload = decode_token("invalid_token")
        
        assert payload is None
    
    def test_token_contains_expiry(self):
        """Test that token contains expiration."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        
        payload = decode_token(token)
        
        assert payload is not None
        assert "exp" in payload
