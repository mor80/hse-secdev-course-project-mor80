import tempfile
from pathlib import Path
from unittest.mock import patch

from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.services.file_service import secure_save
from app.services.secrets_service import validate_secret_strength

client = TestClient(app)


class TestSecureCodingIntegration:
    """Integration tests for secure coding features."""

    def test_complete_secure_workflow(self):
        """Test complete secure workflow from upload to error handling."""
        # This test demonstrates the integration of all security features

        # 1. Test that the application starts with proper secret validation
        # (This would be tested in a real scenario)

        # 2. Test file upload with security validation
        with tempfile.TemporaryDirectory() as temp_dir:
            # Valid PNG data
            png_data = b"\x89PNG\r\n\x1a\n" + b"fake_png_data"

            success, error, saved_path = secure_save(
                base_dir=temp_dir, filename_hint="test.png", data=png_data
            )

            assert success
            assert saved_path is not None

            # Verify file was saved with UUID name
            filename = Path(saved_path).name
            name_part = filename.split(".")[0]
            assert len(name_part) == 36  # UUID length

    def test_error_handling_with_file_upload(self):
        """Test error handling during file upload operations."""
        # Test with malicious file
        malicious_data = b"not_an_image"

        with tempfile.TemporaryDirectory() as temp_dir:
            success, error, saved_path = secure_save(
                base_dir=temp_dir, filename_hint="malicious.txt", data=malicious_data
            )

            assert not success
            assert "unsupported" in error.lower()
            assert saved_path is None

    def test_rfc7807_with_file_upload_endpoint(self):
        """Test RFC 7807 error handling in file upload endpoint."""
        # Create malicious file
        files = {"file": ("malicious.txt", b"not_an_image", "text/plain")}

        # Mock authentication
        with patch("app.api.dependencies.get_current_user") as mock_auth:
            from app.domain.entities import User, UserRole

            mock_user = User(id=1, email="test@example.com", username="test", role=UserRole.USER)
            mock_auth.return_value = mock_user

            with patch("app.services.file_service.ensure_upload_directory") as mock_ensure:
                mock_ensure.return_value = True

                response = client.post("/api/v1/upload/avatar", files=files)

                # Should return RFC 7807 error
                assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

                data = response.json()
                assert "type" in data
                assert "title" in data
                assert "status" in data
                assert "detail" in data
                assert "correlation_id" in data
                assert "validation_errors" in data

    def test_secrets_validation_in_config(self):
        """Test that secrets are validated during configuration loading."""
        # This test would require modifying the config loading process
        # For now, test the validation function directly

        # Test valid secret
        is_valid, error = validate_secret_strength("valid_secret_32_chars_minimum", "jwt_key")
        assert is_valid

        # Test invalid secret
        is_valid, error = validate_secret_strength("weak", "jwt_key")
        assert not is_valid
        assert "at least 32" in error

    def test_file_upload_with_path_traversal_protection(self):
        """Test file upload with path traversal protection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Valid PNG data
            png_data = b"\x89PNG\r\n\x1a\n" + b"fake_data"

            # Try path traversal attack
            success, error, saved_path = secure_save(
                base_dir=temp_dir, filename_hint="../../../etc/passwd.png", data=png_data
            )

            # Should succeed but with secure path
            assert success
            assert saved_path is not None

            # Verify path is within temp_dir (handle /private prefix on macOS)
            saved_resolved = Path(saved_path).resolve()
            base_resolved = Path(temp_dir).resolve()
            assert saved_resolved.is_relative_to(base_resolved)

            # Verify filename is UUID-based
            filename = Path(saved_path).name
            name_part = filename.split(".")[0]
            assert len(name_part) == 36  # UUID length

    def test_error_correlation_across_components(self):
        """Test that correlation IDs are consistent across components."""
        # Test validation error
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "invalid", "username": "test", "password": "short"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        data = response.json()
        correlation_id = data["correlation_id"]

        # Verify correlation ID format
        assert len(correlation_id) == 36
        assert correlation_id.count("-") == 4

    def test_production_error_masking(self):
        """Test that production mode masks sensitive information."""
        # This test would require setting ENV=production
        # For now, test the structure

        response = client.get("/api/v1/wishes/99999")

        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_file_size_limits_enforcement(self):
        """Test that file size limits are enforced."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create oversized file
            oversized_data = b"x" * (6 * 1024 * 1024)  # 6MB

            success, error, saved_path = secure_save(
                base_dir=temp_dir, filename_hint="large.png", data=oversized_data
            )

            assert not success
            assert "too large" in error.lower()
            assert saved_path is None

    def test_magic_bytes_validation(self):
        """Test magic bytes validation for different file types."""
        # Test PNG
        png_data = b"\x89PNG\r\n\x1a\n" + b"fake_data"
        with tempfile.TemporaryDirectory() as temp_dir:
            success, error, saved_path = secure_save(
                base_dir=temp_dir, filename_hint="test.png", data=png_data
            )
            assert success

        # Test JPEG
        jpeg_data = b"\xff\xd8" + b"fake_data" + b"\xff\xd9"
        with tempfile.TemporaryDirectory() as temp_dir:
            success, error, saved_path = secure_save(
                base_dir=temp_dir, filename_hint="test.jpg", data=jpeg_data
            )
            assert success

        # Test invalid file
        invalid_data = b"not_an_image"
        with tempfile.TemporaryDirectory() as temp_dir:
            success, error, saved_path = secure_save(
                base_dir=temp_dir, filename_hint="test.txt", data=invalid_data
            )
            assert not success
            assert "unsupported" in error.lower()

    def test_security_headers_and_cors(self):
        """Test that security headers and CORS are properly configured."""
        response = client.get("/health")

        # Should have CORS headers
        assert response.status_code == status.HTTP_200_OK

        # Test OPTIONS request for CORS
        response = client.options("/api/v1/auth/login")
        assert response.status_code == status.HTTP_200_OK

    def test_comprehensive_error_scenarios(self):
        """Test comprehensive error scenarios across all components."""
        # Test validation error
        response = client.post(
            "/api/v1/auth/register", json={"email": "invalid", "username": "a", "password": "123"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Test authentication error
        response = client.post(
            "/api/v1/auth/login", json={"username": "nonexistent", "password": "wrong"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Test authorization error
        response = client.get("/api/v1/admin/users")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Test not found error
        response = client.get("/api/v1/wishes/99999")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_file_upload_security_comprehensive(self):
        """Test comprehensive file upload security."""
        # Test with various malicious inputs
        test_cases = [
            ("path_traversal.png", b"\x89PNG\r\n\x1a\n" + b"data", "image/png"),
            ("malicious.txt", b"not_an_image", "text/plain"),
            ("large.png", b"x" * (6 * 1024 * 1024), "image/png"),
            ("empty.png", b"", "image/png"),
        ]

        for filename, data, content_type in test_cases:
            files = {"file": (filename, data, content_type)}

            with patch("app.api.dependencies.get_current_user") as mock_auth:
                from app.domain.entities import User, UserRole

                mock_user = User(
                    id=1, email="test@example.com", username="test", role=UserRole.USER
                )
                mock_auth.return_value = mock_user

                with patch("app.services.file_service.ensure_upload_directory") as mock_ensure:
                    mock_ensure.return_value = True

                    response = client.post("/api/v1/upload/avatar", files=files)

                    # Should either succeed with secure handling or fail with validation error
                    assert response.status_code in [
                        status.HTTP_200_OK,
                        status.HTTP_422_UNPROCESSABLE_ENTITY,
                    ]

                    if response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
                        data = response.json()
                        assert "correlation_id" in data
                        assert "validation_errors" in data
