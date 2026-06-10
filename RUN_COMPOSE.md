# RUN_COMPOSE.md - Huong dan chay Lab 05

Tai lieu nay huong dan clone repo sach va chay lai stack Docker Compose cua Lab 05.

## 1. Clone repo

```bash
git clone <repo-url>
cd fit4110-lab5-hong-son-huy
```

## 2. Cai dependencies cho Newman/Prism/Spectral

```bash
npm install
```

## 3. Tao file moi truong

```bash
cp .env.example .env
```

Tren Windows PowerShell:

```powershell
Copy-Item .env.example .env -Force
```

File `.env.example` chi dung gia tri local demo, khong chua secret that.

## 4. Build va chay Docker Compose

Moi truong nay dung duoc `docker-compose` v2:

```bash
docker-compose up -d --build
```

Neu may cua ban ho tro Docker Compose plugin, lenh tuong duong la:

```bash
docker compose up -d --build
```

Stack tao cac container:

- `fit4110-db-lab05` - PostgreSQL tren port 5432
- `fit4110-ai-lab05` - AI mock service tren port 9000
- `fit4110-api-lab05` - FastAPI IoT service tren port 8000

## 5. Kiem tra health/readiness

```bash
curl http://localhost:8000/health
curl http://localhost:9000/health
docker exec -it fit4110-db-lab05 pg_isready -U lab05
```

Kiem tra AI prediction:

```bash
curl -X POST http://localhost:9000/predict
```

Kiem tra API tao reading:

```bash
curl -X POST http://localhost:8000/readings \
  -H "Authorization: Bearer local-dev-token" \
  -H "Content-Type: application/json" \
  -d '{"device_id":"ESP32-LAB-A01","metric":"temperature","value":31.5,"unit":"celsius","timestamp":"2026-05-13T08:30:00+07:00"}'
```

## 6. Chay Newman test

```bash
npm run test:compose
```

Report sinh tai:

```text
reports/newman-lab05-compose.xml
reports/newman-lab05-compose.html
```

## 7. Dung stack

```bash
docker-compose down
```

Xoa kem volume DB khi can reset du lieu:

```bash
docker-compose down -v
```

## 8. Lenh nhanh bang Makefile

```bash
make compose-up
make compose-down
make logs
make test-compose
```

## 9. Goi y go loi

- Dung `docker-compose ps` de xem trang thai container.
- Neu API khong ket noi DB, kiem tra `.env` va health cua `fit4110-db-lab05`.
- Neu AI service can tai model lon, tang `start_period` trong `docker-compose.yml`.
