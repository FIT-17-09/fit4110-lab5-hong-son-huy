# Lab 05 Evidence

Date: 2026-06-10

## Docker Compose

Command:

```powershell
docker-compose up -d --build
docker-compose ps
```

Result:

```text
fit4110-ai-lab05    Up (healthy)   0.0.0.0:9000->9000/tcp
fit4110-api-lab05   Up (healthy)   0.0.0.0:8000->8000/tcp
fit4110-db-lab05    Up (healthy)   0.0.0.0:5432->5432/tcp
```

## Health Checks

```text
GET http://localhost:8000/health -> 200 {"status":"ok","service":"iot-ingestion","version":"0.5.0"}
GET http://localhost:9000/health -> 200 {"status":"ok","service":"ai-service","version":"0.5.0"}
docker exec fit4110-db-lab05 pg_isready -U lab05 -> accepting connections
```

## Newman

Command:

```powershell
npm run test:compose
```

Result:

```text
requests: 5 executed, 0 failed
assertions: 10 executed, 0 failed
average response time: 32ms
```

Generated reports:

```text
reports/newman-lab05-compose.xml
reports/newman-lab05-compose.html
```

## Image Tags

Docker Hub tags pushed:

```text
takemicchi05/iot-ingestion:v0.1.0-team-iot
  digest: sha256:efed062d68d9615a089a5522c4734138567487bfb3ffc4a4dacf55b291fee428

takemicchi05/ai-service:v0.1.0-team-iot
  digest: sha256:9536c2607256dd0f5175d7769fc46bacb029d36c3ba04812d15ed8e24f012b90
```
