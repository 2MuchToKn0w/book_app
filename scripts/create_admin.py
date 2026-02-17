import asyncio
import os

from sqlalchemy import select
from app.database import async_session_maker
from app.models.users import User
from app.auth import hash_password


# Admin data
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin007")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")


async def create_admin():
    async with async_session_maker() as session:
        # Check if an admin already exists
        result = await session.scalars(
            select(User)
            .where(User.email == ADMIN_EMAIL)
        )
        if result.first():
            print("Admin user already exists")
            return

        # Create a new admin
        admin = User(
            email=ADMIN_EMAIL,
            username=ADMIN_USERNAME,
            hashed_password=hash_password(ADMIN_PASSWORD),
            role="admin",
            is_active=True
        )

        session.add(admin)
        await session.commit()
        await session.refresh(admin)

        print(f"Admin user created: {ADMIN_EMAIL}")


if __name__ == "__main__":
    asyncio.run(create_admin())
