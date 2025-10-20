.PHONY: help build start stop restart logs clean test

# Variables
IMAGE_NAME=local-llm-celery
IMAGE_TAG=dev
NETWORK_NAME=llm-net
REDIS_CONTAINER=redis
APP_CONTAINER=llm-app
WORKER_CONTAINER=llm-worker

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build the container image
	podman build -t $(IMAGE_NAME):$(IMAGE_TAG) --format docker .

network: ## Create the podman network
	podman network create $(NETWORK_NAME) || true

start: network ## Start all containers
	@echo "Starting Redis..."
	podman run -d --name $(REDIS_CONTAINER) --network $(NETWORK_NAME) redis:7 || true
	@echo "Starting Flask API..."
	podman run -d --name $(APP_CONTAINER) --network $(NETWORK_NAME) \
		-p 5001:5000 -v $(PWD)/data:/app/data:Z \
		$(IMAGE_NAME):$(IMAGE_TAG) python app.py || true
	@echo "Starting Celery Worker..."
	podman run -d --name $(WORKER_CONTAINER) --network $(NETWORK_NAME) \
		-v $(PWD)/data:/app/data:Z \
		$(IMAGE_NAME):$(IMAGE_TAG) celery -A worker.celery_app worker --loglevel=info || true
	@echo "\nAll services started!"
	@echo "API available at: http://localhost:5001"

stop: ## Stop all containers
	podman stop $(APP_CONTAINER) $(WORKER_CONTAINER) $(REDIS_CONTAINER) 2>/dev/null || true

restart: stop start ## Restart all containers

clean: stop ## Remove all containers and network
	podman rm -f $(APP_CONTAINER) $(WORKER_CONTAINER) $(REDIS_CONTAINER) 2>/dev/null || true
	podman network rm $(NETWORK_NAME) 2>/dev/null || true

logs-app: ## Show Flask API logs
	podman logs -f $(APP_CONTAINER)

logs-worker: ## Show Celery worker logs
	podman logs -f $(WORKER_CONTAINER)

logs-redis: ## Show Redis logs
	podman logs -f $(REDIS_CONTAINER)

ps: ## Show running containers
	podman ps --filter "network=$(NETWORK_NAME)"

test: ## Run a test query
	@echo "Testing API with sample query..."
	curl -X POST http://localhost:5001/analyze \
		-H "Content-Type: application/json" \
		-d '{"question": "What is the median Avg_Price?", "filename": "sales-data.csv"}' \
		| python3 -m json.tool

test-multi: ## Test multi-file analysis
	@echo "Testing multi-file analysis..."
	curl -X POST http://localhost:5001/analyze \
		-H "Content-Type: application/json" \
		-d '{"question": "Load all CSV files and calculate the total combined revenue from all files."}' \
		| python3 -m json.tool

rebuild: clean build start ## Clean, rebuild, and restart everything

shell-app: ## Open shell in Flask API container
	podman exec -it $(APP_CONTAINER) /bin/bash

shell-worker: ## Open shell in Worker container
	podman exec -it $(WORKER_CONTAINER) /bin/bash

# Data management targets
data-list: ## List all data files
	@echo "Listing data files..."
	curl -s http://localhost:5001/data | python3 -m json.tool

data-upload: ## Upload a data file (usage: make data-upload FILE=/path/to/file.csv)
	@if [ -z "$(FILE)" ]; then \
		echo "Error: FILE parameter required"; \
		echo "Usage: make data-upload FILE=/path/to/your/file.csv"; \
		exit 1; \
	fi
	@echo "Uploading $(FILE)..."
	curl -X POST http://localhost:5001/data -F "file=@$(FILE)" | python3 -m json.tool

data-delete: ## Delete a data file (usage: make data-delete NAME=filename.csv)
	@if [ -z "$(NAME)" ]; then \
		echo "Error: NAME parameter required"; \
		echo "Usage: make data-delete NAME=filename.csv"; \
		exit 1; \
	fi
	@echo "Deleting $(NAME)..."
	curl -X DELETE http://localhost:5001/data/$(NAME) | python3 -m json.tool

data-info: ## Get file info (usage: make data-info NAME=filename.csv)
	@if [ -z "$(NAME)" ]; then \
		echo "Error: NAME parameter required"; \
		echo "Usage: make data-info NAME=filename.csv"; \
		exit 1; \
	fi
	curl -s http://localhost:5001/data/$(NAME)/info | python3 -m json.tool

# Kubernetes targets
k8s-deploy: ## Deploy to Kubernetes
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/redis.yaml
	kubectl apply -f k8s/configmap.yaml
	kubectl apply -f k8s/pvc.yaml
	kubectl apply -f k8s/flask-api.yaml
	kubectl apply -f k8s/celery-worker.yaml

k8s-delete: ## Delete from Kubernetes
	kubectl delete namespace llm-analysis

k8s-status: ## Show Kubernetes deployment status
	kubectl get all -n llm-analysis

k8s-logs: ## Show Kubernetes worker logs
	kubectl logs -n llm-analysis -l app=celery-worker --tail=50 -f
