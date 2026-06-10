# Readiness Checklist - Lab 05

- [x] **Database ready:** `fit4110-db-lab05` chay healthy va `pg_isready -U lab05` tra ve accepting connections.
- [x] **AI service ready:** `fit4110-ai-lab05` chay healthy, `GET /health` tra ve 200 va `POST /predict` duoc API goi khi tao reading.
- [x] **API ready:** `fit4110-api-lab05` chay healthy, `GET /health` tra ve 200, tao va lay readings thanh cong voi bearer token hop le.
- [x] **Environment variables:** `.env.example` khai bao `APP_PORT`, `AI_PORT`, `POSTGRES_*`, `DATABASE_URL`, `AI_SERVICE_URL`, `AUTH_TOKEN`, `SERVICE_VERSION`; `.env` local khong commit.
- [x] **Network & Ports:** `team-internal` hoat dong cho giao tiep noi bo; API dung hostname `ai-service`; ports 8000, 9000 va 5432 duoc publish ra host.
- [x] **Image registry push:** images da duoc tag va push len Docker Hub:
  `takemicchi05/iot-ingestion:v0.1.0-team-iot` va `takemicchi05/ai-service:v0.1.0-team-iot`.

## Evidence

- `docker-compose ps`: 3 container `fit4110-api-lab05`, `fit4110-ai-lab05`, `fit4110-db-lab05` deu `healthy`.
- Newman compose run: 5 requests, 10 assertions, 0 failed.
- Docker Hub images pushed:
  - `takemicchi05/iot-ingestion:v0.1.0-team-iot`
  - `takemicchi05/ai-service:v0.1.0-team-iot`
- Reports:
  - `reports/newman-lab05-compose.xml`
  - `reports/newman-lab05-compose.html`
