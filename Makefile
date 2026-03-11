docker-old-up:
	docker-compose -f apps/docker-compose.yml up -d --build
	docker ps | grep smarthome-app

docker-new-up:
	docker-compose -f docker/docker-compose.yml up -d --build
	docker ps | grep smart_home

docker-new-restart:
	docker-compose -f docker/docker-compose.yml down
	docker-compose -f docker/docker-compose.yml up -d
	docker ps | grep smart_home

docker-new-up-only-infra:
	docker-compose -f docker/docker-compose.yml up -d kafka kafka-ui kafka-init postgres valkey minio mosquitto
	docker ps | grep smart_home

docker-up-all: docker-old-up docker-new-up