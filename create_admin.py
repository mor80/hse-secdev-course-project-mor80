import asyncio

from app.adapters.database import AsyncSessionLocal
from app.adapters.repositories.user_repository import UserRepository
from app.domain.entities import UserRole
from app.domain.models import UserCreate
from app.services.auth_service import get_password_hash


async def create_admin():
    email = input("Enter admin email: ")
    username = input("Enter admin username: ")
    password = input("Enter admin password: ")

    async with AsyncSessionLocal() as db:
        repository = UserRepository(db)

        existing_user = await repository.get_by_email(email)
        if existing_user:
            print(f"User with email {email} already exists")
            return

        existing_user = await repository.get_by_username(username)
        if existing_user:
            print(f"User with username {username} already exists")
            return

        user_data = UserCreate(email=email, username=username, password=password)
        hashed_password = get_password_hash(password)

        admin_user = await repository.create(user_data, hashed_password, role=UserRole.ADMIN)

        print("Admin user created successfully!")
        print(f"ID: {admin_user.id}")
        print(f"Email: {admin_user.email}")
        print(f"Username: {admin_user.username}")
        print(f"Role: {admin_user.role}")


if __name__ == "__main__":
    asyncio.run(create_admin())
