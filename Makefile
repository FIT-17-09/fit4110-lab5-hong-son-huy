# ============================================================
# FIT4110 Lab05 - Makefile
# ============================================================

.PHONY: compose-up compose-down logs test-compose health clean

## Khởi động toàn bộ stack (build + run detached)
compose-up:
	docker compose up -d --build

## Dừng và xóa toàn bộ stack
compose-down:
	docker compose down

## Dừng và xóa cả volume
compose-clean:
	docker compose down -v

## Theo dõi log tất cả service
logs:
	docker compose logs -f

## Theo dõi log của từng service
logs-api:
	docker compose logs -f api

logs-db:
	docker compose logs -f db

logs-ai:
	docker compose logs -f ai-service

## Kiểm tra health của từng service
health:
	@echo "=== API Health ==="
	@curl -s http://localhost:8000/health | python3 -m json.tool
	@echo ""
	@echo "=== AI Service Health ==="
	@curl -s http://localhost:9000/health | python3 -m json.tool
	@echo ""
	@echo "=== DB Health ==="
	@docker exec fit4110-db-lab05 pg_isready -U $${POSTGRES_USER:-lab05}

## Chạy Newman test trên stack Compose
test-compose:
	@mkdir -p reports
	npx newman run postman/collections/FIT4110_lab05_local.postman_collection.json \
		--environment postman/environments/FIT4110_lab05_local.postman_environment.json \
		--reporters cli,htmlextra,junit \
		--reporter-htmlextra-export reports/newman-lab05-compose.html \
		--reporter-junit-export reports/newman-lab05-compose.xml \
		--reporter-htmlextra-title "FIT4110 Lab05 - Smart Campus Gate API" \
		--color on

## Cài Newman và reporter
install-newman:
	npm install -g newman newman-reporter-htmlextra newman-reporter-junit

## Chạy API local không dùng Docker
run-local:
	python -m venv .venv && \
	source .venv/bin/activate && \
	pip install -r requirements.txt && \
	uvicorn iot_app.main:app --app-dir src --host 0.0.0.0 --port 8000

## Xem trạng thái container
ps:
	docker compose ps

## Help
help:
	@echo "Các lệnh có sẵn:"
	@echo "  make compose-up     - Build và chạy toàn bộ stack"
	@echo "  make compose-down   - Dừng stack"
	@echo "  make compose-clean  - Dừng stack và xóa volume"
	@echo "  make logs           - Xem log tất cả service"
	@echo "  make health         - Kiểm tra health tất cả service"
	@echo "  make test-compose   - Chạy Newman test"
	@echo "  make install-newman - Cài Newman và reporter"
	@echo "  make ps             - Xem trạng thái container"