#!/usr/bin/env python
import os
import sys


def check_python_version():
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ required")
        return False
    print(
        f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    return True


def check_env_file():
    if os.path.exists(".env"):
        print("✅ .env file exists")
        return True
    print("❌ .env file not found. Run: ./setup_env.sh")
    return False


def check_dependencies():
    try:
        import alembic  # noqa: F401
        import asyncpg  # noqa: F401
        import fastapi  # noqa: F401
        import sqlalchemy  # noqa: F401

        print("✅ Main dependencies installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: pip install -r requirements.txt")
        return False


def check_dev_dependencies():
    try:
        import httpx  # noqa: F401
        import pytest  # noqa: F401

        print("✅ Dev dependencies installed")
        return True
    except ImportError as e:
        print(f"⚠️  Missing dev dependency: {e}")
        print("Run: pip install -r requirements-dev.txt")
        return False


def check_docker():
    import subprocess

    try:
        result = subprocess.run(
            ["docker", "--version"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            print(f"✅ Docker: {result.stdout.strip()}")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    print("⚠️  Docker not found or not running")
    return False


def check_postgres():
    import subprocess

    try:
        result = subprocess.run(
            ["docker", "compose", "ps", "db"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if "Up" in result.stdout:
            print("✅ PostgreSQL container is running")
            return True
        else:
            print("⚠️  PostgreSQL container not running. Run: docker compose up -d db")
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("⚠️  Cannot check PostgreSQL status")
        return False


def main():
    print("🔍 Checking Wishlist API setup...\n")

    checks = [
        ("Python version", check_python_version()),
        (".env file", check_env_file()),
        ("Dependencies", check_dependencies()),
        ("Dev dependencies", check_dev_dependencies()),
        ("Docker", check_docker()),
        ("PostgreSQL", check_postgres()),
    ]

    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)

    passed = sum(1 for _, result in checks if result)
    total = len(checks)

    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\n✅ Everything looks good! You can start developing.")
        print("\nNext steps:")
        print("  1. Run migrations: alembic upgrade head")
        print("  2. Create admin: python create_admin.py")
        print("  3. Start server: uvicorn app.main:app --reload")
    else:
        print("\n⚠️  Some checks failed. Please fix them before starting.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
