.PHONY: deps lint shell migration migrate_current migrate_up migrate_down server test test_once postgres_up postgres_down docker_up docker_down

deps:
	poetry install

lint:
	poetry run ruff check . 

shell:
	poetry run python

migration:
	if [ -z "$(m)" ]; then echo "Migration message is required. Use: make migration m='your message'"; exit 1; fi
	poetry run alembic revision -m "$(m)"

migrate_current:
	poetry run alembic current

migrate_up:
	poetry run alembic upgrade head

migrate_down:
	poetry run alembic downgrade -1

server:
	ENV=STAGE poetry run python app.py

test:
	export DATABASE_URL=$${DATABASE_URL}_test; \
	poetry run alembic upgrade head; \
	poetry run -- ptw -- -s -vv $(args)

test_once:
	export DATABASE_URL=$${DATABASE_URL}_test; \
	poetry run alembic upgrade head; \
	poetry run pytest -s

postgres_up:
	docker-compose -f docker-compose-postgres.yml up -d

postgres_down:
	docker-compose -f docker-compose-postgres.yml down

docker_up:
	docker build -t exam-depository . && docker run -d -e ENV=PROD -e AUTH_TOKEN=$${AUTH_TOKEN} -e DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:5432/exam_depository_dev -e PORT=$${PORT} -p $${PORT}:$${PORT} exam-depository

docker_down:
	docker ps -a -q --filter ancestor=exam-depository | xargs -I {} sh -c 'docker stop {} && docker rm {}'