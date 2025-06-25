.PHONY: setup build up down logs shell migrate upgrade shell-db test clean

# Initialize the project
setup:
	docker-compose build
	docker-compose up -d db
	sleep 5  # Wait for database to be ready
	docker-compose run --rm web flask db init
	docker-compose run --rm web flask db migrate -m "Initial migration"
	docker-compose run --rm web flask db upgrade

# Build containers
build:
	docker-compose build

# Start services
up:
	docker-compose up -d

# Stop services
down:
	docker-compose down

# View logs
logs:
	docker-compose logs -f

# Open shell in web container
shell:
	docker-compose exec web bash

# Database migrations
migrate:
	docker-compose run --rm web flask db migrate -m "$(m)"

# Apply migrations
upgrade:
	docker-compose run --rm web flask db upgrade

# Open database shell
shell-db:
	docker-compose exec db psql -U postgres -d rebox_mail

# Run tests
test:
	docker-compose run --rm web python -m pytest

# Clean up
clean:
	docker-compose down -v
	rm -f .coverage
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +
