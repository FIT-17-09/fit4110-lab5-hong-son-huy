FIT4110 Lab05 — Test reports and evidence

Summary
- Newman end-to-end tests ran against the Compose stack and passed: 15 requests, 0 failures, 41 assertions.
- Health checks: API, AI service, and PostgreSQL reported healthy when tested locally.

Artifacts produced
- HTML report: reports/newman-lab05-compose.html
- JUnit XML: reports/newman-lab05-compose.xml
- Evidence logs: reports/evidence/api.log, reports/evidence/ai.log
- Health snapshot: reports/evidence/health.json
- Screenshot (if available): reports/images/health.png

How to reproduce
1. Copy example env:

```bash
cp .env.example .env
```

2. Build and run the stack:

```bash
docker compose up -d --build
```

3. Wait until DB and AI service are healthy, then run tests:

```bash
make test-compose
# or
npm run test:compose
```

Notes
- `reports/` may be ignored by git in this repo; the summary file `reports/README.md` is intended to be tracked so reviewers can quickly find the artifacts locally.
- Do not commit real secrets; `.env` is not tracked by git.
