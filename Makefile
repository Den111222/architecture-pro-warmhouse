docker-old-up:
	docker-compose -f apps/docker-compose.yml up -d --build
	docker ps | grep smarthome-app

docker-new-up:
	docker-compose -f docker/docker-compose.yml up -d --build
	docker ps | grep smart_home