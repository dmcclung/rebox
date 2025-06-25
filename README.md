# rebox

A passwordless authentication system for mail servers.

## Prerequisites

- Docker and Docker Compose
- Python 3.10+

## Installation

1. Clone the repository
2. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
3. Update the `.env` file with your configuration

## Development with Docker

### First-time setup

```bash
make setup
```

This will:
1. Build the Docker containers
2. Start the database
3. Initialize and apply database migrations

### Common Commands

```bash
# Start all services
make up

# Stop all services
make down

# View logs
make logs

# Create a new database migration
make migrate m="your migration message"

# Apply pending migrations
make upgrade

# Open a shell in the web container
make shell

# Open a PostgreSQL shell
make shell-db

# Run tests
make test

# Clean up containers and temporary files
make clean
```

## Manual Commands

If you prefer not to use the Makefile, here are the equivalent Docker commands:

```bash
# Build containers
docker-compose build

# Start services
docker-compose up -d

# Initialize migrations (first time only)
docker-compose run --rm web flask db init

# Create a new migration
docker-compose run --rm web flask db migrate -m "Your migration message"

# Apply migrations
docker-compose run --rm web flask db upgrade
```

## Configuration

Update the `.env` file with your configuration. Important variables:

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Secret key for session management
- `RP_ID`: Relying Party ID for WebAuthn
- `RP_NAME`: Display name for WebAuthn prompts

Generate a secure `SECRET_KEY` with:
```bash
openssl rand -hex 32
```

## Running without Docker

For local development without Docker:

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the application:
   ```bash
   flask run
   ```

## License

MIT
