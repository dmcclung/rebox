.PHONY: build up down db logs shell migrate upgrade shell-db test clean restart rebuild

# Restart web service
restart:
	docker-compose restart web

# Rebuild and restart web service
rebuild:
	docker-compose up -d --build web

# Build containers
build:
	docker-compose build

# Start services
up:
	docker-compose up -d

# Stop services
down:
	docker-compose down

# Start database
db:
	docker-compose up -d db

# View logs
logs:
	docker-compose logs -f

# Open shell in web container
shell:
	docker-compose exec web bash

# Database migrations
migrate:
	flask db migrate -m "$(m)"

# Apply migrations
upgrade:
	flask db upgrade

# Open database shell
shell-db:
	docker-compose exec db psql -U postgres -d rebox_mail

# Run tests
test:
	flask test

# Clean up
clean:
	docker-compose down -v
	rm -f .coverage
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +
