# Run the app stack
up:
	docker compose up --build -d

# Stop all containers
down:
	docker compose down --remove-orphans

# Show logs from the web container
logs:
	docker logs -f agentic_rag_fastapi-web-1

# Run create_doctor.py inside the web container
create-doctor:
	docker exec -it agentic_rag_fastapi-web-1 python scripts/create_doctor.py
