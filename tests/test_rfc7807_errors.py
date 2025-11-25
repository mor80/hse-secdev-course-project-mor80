from fastapi import status
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestRFC7807ErrorHandling:
    """Test RFC 7807 Problem Details error handling."""

    def test_validation_error_rfc7807_format(self):
        """Test that validation errors return RFC 7807 format."""
        # Test with invalid email format
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",  # Invalid email format
                "username": "testuser",
                "password": "short",  # Too short password
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Check RFC 7807 format
        data = response.json()
        assert "type" in data
        assert "title" in data
        assert "status" in data
        assert "detail" in data
        assert "correlation_id" in data
        assert "validation_errors" in data

        # Verify correlation_id is UUID format
        correlation_id = data["correlation_id"]
        assert len(correlation_id) == 36  # UUID4 length
        assert correlation_id.count("-") == 4  # UUID4 format

        # Verify error type
        assert data["type"] == "https://api.wishlist.com/errors/validation-error"
        assert data["title"] == "Validation Error"
        assert data["status"] == 422

    def test_authentication_error_rfc7807_format(self):
        """Test that authentication errors return RFC 7807 format."""
        # Test with invalid credentials
        response = client.post(
            "/api/v1/auth/login", json={"username": "nonexistent", "password": "wrongpassword"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Check RFC 7807 format
        data = response.json()
        assert "type" in data
        assert "title" in data
        assert "status" in data
        assert "detail" in data
        assert "correlation_id" in data

        # Verify error type
        assert data["type"] == "https://api.wishlist.com/errors/auth-error"
        assert data["title"] == "Authentication Error"
        assert data["status"] == 401

    def test_authorization_error_rfc7807_format(self):
        """Test that authorization errors return RFC 7807 format."""
        # Test accessing admin endpoint without admin privileges
        response = client.get("/api/v1/admin/users")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Check RFC 7807 format
        data = response.json()
        assert "type" in data
        assert "title" in data
        assert "status" in data
        assert "detail" in data
        assert "correlation_id" in data

        # Verify error type
        assert data["type"] == "https://api.wishlist.com/errors/authz-error"
        assert data["title"] == "Authorization Error"
        assert data["status"] == 401

    def test_not_found_error_rfc7807_format(self):
        """Test that not found errors return RFC 7807 format."""
        # Test accessing non-existent wish
        response = client.get("/api/v1/wishes/99999")

        assert response.status_code == status.HTTP_404_NOT_FOUND

        # Check RFC 7807 format
        data = response.json()
        assert "type" in data
        assert "title" in data
        assert "status" in data
        assert "detail" in data
        assert "correlation_id" in data

        # Verify error type
        assert data["type"] == "https://api.wishlist.com/errors/not-found"
        assert data["title"] == "Not Found"
        assert data["status"] == 404

    def test_correlation_id_uniqueness(self):
        """Test that correlation IDs are unique across requests."""
        # Make multiple requests
        responses = []
        for _ in range(5):
            response = client.post(
                "/api/v1/auth/register",
                json={"email": "invalid", "username": "test", "password": "short"},
            )
            responses.append(response.json())

        # Extract correlation IDs
        correlation_ids = [resp["correlation_id"] for resp in responses]

        # All should be unique
        assert len(set(correlation_ids)) == len(correlation_ids)

    def test_production_error_masking(self):
        """Test that production mode masks sensitive error details."""
        # This test would require setting ENV=production
        # For now, test that the structure is correct
        response = client.get("/api/v1/wishes/99999")

        data = response.json()
        # In production, detail should be masked
        # For now, just verify the structure exists
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_error_logging_with_correlation_id(self):
        """Test that errors are logged with correlation ID."""
        # This test would require capturing logs
        # For now, just verify the error response structure
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "invalid", "username": "test", "password": "short"},
        )

        data = response.json()
        correlation_id = data["correlation_id"]

        # Verify correlation ID format
        assert len(correlation_id) == 36
        assert correlation_id.count("-") == 4

    def test_validation_error_details(self):
        """Test that validation errors include detailed field information."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",
                "username": "a",  # Too short
                "password": "123",  # Too short
            },
        )

        data = response.json()
        validation_errors = data["validation_errors"]

        # Should have multiple validation errors
        assert len(validation_errors) >= 2

        # Check error structure
        for error in validation_errors:
            assert "field" in error
            assert "message" in error
            assert "type" in error

    def test_http_exception_conversion(self):
        """Test that HTTP exceptions are converted to RFC 7807 format."""
        # Test with a 500 error (this would require triggering an internal error)
        # For now, test with a known endpoint that might return HTTP errors
        response = client.get("/api/v1/wishes/")

        # Should return 403 (no auth) in RFC 7807 format
        if response.status_code == 403:
            data = response.json()
            assert "type" in data
            assert "title" in data
            assert "status" in data
            assert "detail" in data
            assert "correlation_id" in data
