FILENAME = klara-bot.zip
run:
	python3 ./bot.py

build:
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