export DOCKER_DEFAULT_PLATFORM=linux/amd64

storage:
		docker compose -f docker-compose.yml up --build --force-recreate -d redis && sleep 10

up:
	docker compose -f docker-compose.yml --profile all_containers up --build --force-recreate -d

down:
	docker compose -f docker-compose.yml --profile all_containers down;

manage:
	docker compose -f docker-compose.yml up -d manage_users --build --force-recreate; docker exec -ti manage_container python ./manage.py; docker compose -f docker-compose.yml down  manage_users
