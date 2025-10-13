#!/bin/bash

ENV_FILE=".env"

if [ -f "$ENV_FILE" ]; then
    echo "⚠️  .env file already exists. Backup will be created."
    cp "$ENV_FILE" "${ENV_FILE}.backup.$(date +%s)"
fi

cat > "$ENV_FILE" << 'EOF'
APP_NAME=Wishlist API
ENV=local
DEBUG=False

SECRET_KEY=dev-secret-key-change-in-production-use-strong-random-secret-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

DATABASE_URL=postgresql+asyncpg://wishlist_user:wishlist_pass@localhost:5432/wishlist_db

POSTGRES_DB=wishlist_db
POSTGRES_USER=wishlist_user
POSTGRES_PASSWORD=wishlist_pass

CORS_ORIGINS=
EOF

echo "✅ .env file created successfully!"
echo ""
echo "📝 Next steps:"
echo "   1. Review and edit .env file if needed"
echo "   2. Start PostgreSQL: docker compose up -d db"
echo "   3. Run migrations: alembic upgrade head"
echo "   4. Create admin user: python create_admin.py"
echo "   5. Start app: uvicorn app.main:app --reload"
echo ""
echo "Or run everything with Docker:"
echo "   docker compose up --build"
