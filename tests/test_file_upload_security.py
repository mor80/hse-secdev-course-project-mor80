import tempfile
from pathlib import Path
from unittest.mock import patch

from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.services.file_service import (
    secure_save,
    sniff_image_type,
    validate_file_size,
    validate_file_type,
)

client = TestClient(app)


class TestFileUploadSecurity:
    """Test secure file upload functionality."""

    def test_png_magic_bytes_detection(self):
        """Test PNG file detection by magic bytes."""
        # Valid PNG header
        png_data = b"\x89PNG\r\n\x1a\n" + b"fake_png_data"

        detected_type = sniff_image_type(png_data)
        assert detected_type == "image/png"

    def test_jpeg_magic_bytes_detection(self):
        """Test JPEG file detection by magic bytes."""
        # Valid JPEG header and footer
        jpeg_data = b"\xff\xd8" + b"fake_jpeg_data" + b"\xff\xd9"

        detected_type = sniff_image_type(jpeg_data)
        assert detected_type == "image/jpeg"

    def test_invalid_file_type_detection(self):
        """Test detection of invalid file types."""
        # Invalid data
        invalid_data = b"not_an_image_at_all"

        detected_type = sniff_image_type(invalid_data)
        assert detected_type is None

    def test_empty_file_detection(self):
        """Test detection of empty files."""
        empty_data = b""

        detected_type = sniff_image_type(empty_data)
        assert detected_type is None

    def test_file_size_validation_positive(self):
        """Test valid file size validation."""
        # Small file (1KB)
        small_data = b"x" * 1024

        is_valid, error = validate_file_size(small_data)
        assert is_valid
        assert error == ""

    def test_file_size_validation_negative(self):
        """Test file size validation with oversized file."""
        # Oversized file (6MB)
        oversized_data = b"x" * (6 * 1024 * 1024)

        is_valid, error = validate_file_size(oversized_data)
        assert not is_valid
        assert "too large" in error.lower()

    def test_empty_file_size_validation(self):
        """Test file size validation with empty file."""
        empty_data = b""

        is_valid, error = validate_file_size(empty_data)
        assert not is_valid
        assert "empty" in error.lower()

    def test_file_type_validation_positive(self):
        """Test valid file type validation."""
        # Valid PNG
        png_data = b"\x89PNG\r\n\x1a\n" + b"fake_data"

        is_valid, error = validate_file_type(png_data)
        assert is_valid
        assert error == ""

    def test_file_type_validation_negative(self):
        """Test file type validation with invalid type."""
        # Invalid file type
        invalid_data = b"not_an_image"

        is_valid, error = validate_file_type(invalid_data)
        assert not is_valid
        assert "unsupported" in error.lower()

    def test_secure_save_positive(self):
        """Test successful secure file save."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Valid PNG data
            png_data = b"\x89PNG\r\n\x1a\n" + b"fake_png_data"

            success, error, saved_path = secure_save(
                base_dir=temp_dir, filename_hint="test.png", data=png_data
            )

            assert success
            assert error == ""
            assert saved_path is not None
            assert Path(saved_path).exists()

    def test_secure_save_oversized_file(self):
        """Test secure save with oversized file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Oversized file
            oversized_data = b"x" * (6 * 1024 * 1024)

            success, error, saved_path = secure_save(
                base_dir=temp_dir, filename_hint="large.png", data=oversized_data
            )

            assert not success
            assert "too large" in error.lower()
            assert saved_path is None

    def test_secure_save_invalid_type(self):
        """Test secure save with invalid file type."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Invalid file type
            invalid_data = b"not_an_image"

            success, error, saved_path = secure_save(
                base_dir=temp_dir, filename_hint="test.txt", data=invalid_data
            )

            assert not success
            assert "unsupported" in error.lower()
            assert saved_path is None

    def test_secure_save_path_traversal_protection(self):
        """Test protection against path traversal attacks."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Valid PNG data
            png_data = b"\x89PNG\r\n\x1a\n" + b"fake_data"

            # Try to use path traversal in filename hint
            success, error, saved_path = secure_save(
                base_dir=temp_dir, filename_hint="../../../etc/passwd", data=png_data
            )

            # Should still succeed but with secure filename
            assert success
            assert saved_path is not None
            # Saved path should be within temp_dir
            saved_resolved = Path(saved_path).resolve()
            base_resolved = Path(temp_dir).resolve()
            assert saved_resolved.is_relative_to(base_resolved)

    def test_secure_save_uuid_filename(self):
        """Test that saved files use UUID filenames."""
        with tempfile.TemporaryDirectory() as temp_dir:
            png_data = b"\x89PNG\r\n\x1a\n" + b"fake_data"

            success, error, saved_path = secure_save(
                base_dir=temp_dir, filename_hint="sensitive_filename.png", data=png_data
            )

            assert success
            filename = Path(saved_path).name

            # Should be UUID + extension
            name_part = filename.split(".")[0]
            assert len(name_part) == 36  # UUID length
            assert name_part.count("-") == 4  # UUID format

    def test_upload_endpoint_authentication_required(self):
        """Test that upload endpoint requires authentication."""
        # Create a fake file
        files = {"file": ("test.png", b"fake_image_data", "image/png")}

        response = client.post("/api/v1/upload/avatar", files=files)

        # Should require authentication
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @patch("app.services.file_service.ensure_upload_directory")
    def test_upload_endpoint_validation_error(self, mock_ensure_dir):
        """Test upload endpoint with validation error."""
        mock_ensure_dir.return_value = True

        # Create a fake file with invalid content
        files = {"file": ("test.txt", b"not_an_image", "text/plain")}

        # Mock authentication
        with patch("app.api.dependencies.get_current_user") as mock_auth:
            from app.domain.entities import User, UserRole

            mock_user = User(id=1, email="test@example.com", username="test", role=UserRole.USER)
            mock_auth.return_value = mock_user

            response = client.post("/api/v1/upload/avatar", files=files)

            # Should return validation error in RFC 7807 format
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

            data = response.json()
            assert "type" in data
            assert "title" in data
            assert "status" in data
            assert "detail" in data
            assert "correlation_id" in data

    def test_upload_endpoint_oversized_file(self):
        """Test upload endpoint with oversized file."""
        # Create a large file (6MB)
        large_data = b"x" * (6 * 1024 * 1024)
        files = {"file": ("large.png", large_data, "image/png")}

        # Mock authentication
        with patch("app.api.dependencies.get_current_user") as mock_auth:
            from app.domain.entities import User, UserRole

            mock_user = User(id=1, email="test@example.com", username="test", role=UserRole.USER)
            mock_auth.return_value = mock_user

            response = client.post("/api/v1/upload/avatar", files=files)

            # Should return validation error
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

            data = response.json()
            assert "validation_errors" in data
            # Check that the error mentions file size
            validation_errors = data["validation_errors"]
            assert any("too large" in error["message"].lower() for error in validation_errors)

    def test_upload_endpoint_malicious_filename(self):
        """Test upload endpoint with malicious filename."""
        # Create valid PNG data but with malicious filename
        png_data = b"\x89PNG\r\n\x1a\n" + b"fake_data"
        files = {"file": ("../../../etc/passwd.png", png_data, "image/png")}

        # Mock authentication
        with patch("app.api.dependencies.get_current_user") as mock_auth:
            from app.domain.entities import User, UserRole

            mock_user = User(id=1, email="test@example.com", username="test", role=UserRole.USER)
            mock_auth.return_value = mock_user

            with patch("app.services.file_service.secure_save") as mock_save:
                mock_save.return_value = (True, "", "/secure/path/file.png")

                response = client.post("/api/v1/upload/avatar", files=files)

                # Should succeed but with secure filename
                assert response.status_code == status.HTTP_200_OK

                # Verify secure_save was called with the malicious filename
                mock_save.assert_called_once()
                call_args = mock_save.call_args
                assert "passwd" in call_args[1]["filename_hint"]  # Original filename passed
