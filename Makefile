FILENAME = klara-bot.zip
run:
	python3 ./bot/bot.py 
	
run_logger:
	python3 ./log_service/main.py

build:
	cd bot
	cp .env.prod env-prod
	zip -ur $(FILENAME) . \
	-x ".venv/*" \
	-x "__pycache__/*" \
	-x ".git*" \
	-x ".env*"
	rm env-prod

deploy:
	mv env-prod .env.prod
	docker compose up --build

compose:
	docker compose up -d --build

dev:
	docker-compose up -d --build