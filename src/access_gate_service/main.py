"""
Smart Campus Access Gate & Core Business API — FIT4110 Lab 05
Endpoints theo OpenAPI contract của team-gate:
  GET  /health
  POST /access/check
  GET  /decisions/{decisionId}
  GET  /policies/access/{policyId}
  GET  /access/logs/recent
  GET  /access/logs/{logId}
  GET  /gates/{gateId}/status
  GET  /cards/{cardId}
"""
import os
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from http import HTTPStatus
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# ── Biến môi trường ──────────────────────────────────────────
SERVICE_NAME = os.getenv("SERVICE_NAME", "access-gate")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "0.5.0-team-gate")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "local-dev-token")

# ── App ──────────────────────────────────────────────────────
app = FastAPI(
    title="FIT4110 Lab 05 - Access Gate API",
    version=SERVICE_VERSION,
    description=(
        "Access Gate và Core Business API chạy trong Docker Compose cho Lab 05. "
        "Quản lý kiểm soát vào/ra cổng thông qua thẻ RFID và chính sách truy cập."
    ),
)


# ── Enums ────────────────────────────────────────────────────
class Direction(str, Enum):
    IN = "IN"
    OUT = "OUT"


class AccessStatus(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"


class GateStatusEnum(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    MAINTENANCE = "MAINTENANCE"


class CardStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    EXPIRED = "EXPIRED"


# ── Schemas ──────────────────────────────────────────────────
class ProblemDetails(BaseModel):
    type: str = "about:blank"
    title: str
    status: int = Field(..., ge=400, le=599)
    detail: str
    instance: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class AccessCheckRequest(BaseModel):
    cardId: str = Field(..., examples=["RFID-001"])
    gateId: str = Field(..., examples=["GATE-01"])
    timestamp: Optional[str] = Field(default=None, examples=["2026-06-10T08:30:00+07:00"])


class AccessGranted(BaseModel):
    decisionType: str = "ALLOW"
    decisionId: str
    allow: bool = True
    policyId: Optional[str] = None
    expiresAt: Optional[str] = None


class AccessDenied(BaseModel):
    decisionType: str = "DENY"
    decisionId: str
    allow: bool = False
    reasonCode: str = "CARD_BLOCKED"


class AccessPolicy(BaseModel):
    policyId: str
    role: str
    accessLevel: Optional[str] = None


class AccessLog(BaseModel):
    logId: str
    cardId: str
    gateId: str
    direction: Direction
    status: AccessStatus
    timestamp: str
    operatorNote: Optional[str] = None


class GateStatus(BaseModel):
    gateId: str
    status: GateStatusEnum
    lastUpdated: Optional[str] = None


class CardInfo(BaseModel):
    cardId: str
    ownerName: str
    cardStatus: CardStatusEnum
    expiresAt: Optional[str] = None


# ── In-memory stores ─────────────────────────────────────────
DECISIONS: List[Dict] = []
ACCESS_LOGS: List[Dict] = []

# Dữ liệu mẫu cố định (seed data)
POLICIES: Dict[str, Dict] = {
    "POLICY-01": {"policyId": "POLICY-01", "role": "Student", "accessLevel": "NORMAL"},
    "POLICY-02": {"policyId": "POLICY-02", "role": "Staff", "accessLevel": "ELEVATED"},
    "POLICY-03": {"policyId": "POLICY-03", "role": "Admin", "accessLevel": "FULL"},
}

GATES: Dict[str, Dict] = {
    "GATE-01": {"gateId": "GATE-01", "status": "CLOSED", "lastUpdated": "2026-06-10T00:00:00+00:00"},
    "GATE-02": {"gateId": "GATE-02", "status": "OPEN", "lastUpdated": "2026-06-10T00:00:00+00:00"},
    "GATE-03": {"gateId": "GATE-03", "status": "MAINTENANCE", "lastUpdated": "2026-06-10T00:00:00+00:00"},
}

CARDS: Dict[str, Dict] = {
    "RFID-001": {"cardId": "RFID-001", "ownerName": "Nguyen Van A", "cardStatus": "ACTIVE", "expiresAt": "2027-12-31T23:59:59+07:00"},
    "RFID-002": {"cardId": "RFID-002", "ownerName": "Tran Thi B", "cardStatus": "ACTIVE", "expiresAt": "2027-06-30T23:59:59+07:00"},
    "RFID-BLOCKED": {"cardId": "RFID-BLOCKED", "ownerName": "Le Van C", "cardStatus": "BLOCKED", "expiresAt": None},
    "RFID-EXPIRED": {"cardId": "RFID-EXPIRED", "ownerName": "Pham Thi D", "cardStatus": "EXPIRED", "expiresAt": "2025-01-01T00:00:00+07:00"},
}


# ── Helpers ───────────────────────────────────────────────────
def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_uuid() -> str:
    return str(uuid.uuid4())


def build_problem(
    *,
    status_code: int,
    title: str,
    detail: str,
    instance: Optional[str] = None,
    problem_type: str = "about:blank",
) -> Dict:
    problem = {
        "type": problem_type,
        "title": title,
        "status": status_code,
        "detail": detail,
    }
    if instance:
        problem["instance"] = instance
    return problem


# ── Exception handlers ────────────────────────────────────────
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        problem = exc.detail
    else:
        title = "HTTP Error"
        try:
            title = HTTPStatus(exc.status_code).phrase
        except Exception:
            pass
        problem = build_problem(
            status_code=exc.status_code,
            title=title,
            detail=str(exc.detail),
            instance=str(request.url.path),
        )

    problem.setdefault("status", exc.status_code)
    problem.setdefault("title", problem.get("title", HTTPStatus(exc.status_code).phrase if exc.status_code in HTTPStatus.__members__.values() else "HTTP Error"))
    problem.setdefault("type", "about:blank")
    problem.setdefault("detail", "Request failed")
    problem.setdefault("instance", str(request.url.path))

    return JSONResponse(
        status_code=exc.status_code,
        content=problem,
        media_type="application/problem+json",
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    first_error = exc.errors()[0] if exc.errors() else {}
    location = ".".join(str(item) for item in first_error.get("loc", []))
    message = first_error.get("msg", "Request validation error")
    detail = f"{location}: {message}" if location else message

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=build_problem(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            title="Validation error",
            detail=detail,
            instance=str(request.url.path),
            problem_type="https://smart-campus.local/problems/validation-error",
        ),
        media_type="application/problem+json",
    )


# ── Auth ──────────────────────────────────────────────────────
def verify_bearer_token(authorization: Optional[str] = Header(default=None)) -> None:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=build_problem(
                status_code=status.HTTP_401_UNAUTHORIZED,
                title="Unauthorized",
                detail="Missing Authorization header",
                problem_type="https://smart-campus.local/problems/unauthorized",
            ),
        )
    expected = f"Bearer {AUTH_TOKEN}"
    if authorization != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=build_problem(
                status_code=status.HTTP_401_UNAUTHORIZED,
                title="Unauthorized",
                detail="Invalid bearer token",
                problem_type="https://smart-campus.local/problems/unauthorized",
            ),
        )


# ── Endpoints ─────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service=SERVICE_NAME, version=SERVICE_VERSION)


@app.post(
    "/access/check",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_bearer_token)],
    responses={
        401: {"model": ProblemDetails},
        422: {"model": ProblemDetails},
    },
)
def check_access(payload: AccessCheckRequest, request: Request) -> Dict:
    """
    Kiểm tra quyền truy cập: cardId + gateId → ALLOW hoặc DENY.
    Logic:
      - Card không tồn tại → DENY (CARD_NOT_FOUND)
      - Card BLOCKED       → DENY (CARD_BLOCKED)
      - Card EXPIRED       → DENY (CARD_EXPIRED)
      - Card ACTIVE        → ALLOW
    Sau đó ghi vào access log.
    """
    timestamp = payload.timestamp or now_iso()
    decision_id = new_uuid()
    log_id = new_uuid()

    card = CARDS.get(payload.cardId)

    if card is None:
        decision = {
            "decisionType": "DENY",
            "decisionId": decision_id,
            "allow": False,
            "reasonCode": "CARD_NOT_FOUND",
        }
        log_status = "DENY"
    elif card["cardStatus"] == "BLOCKED":
        decision = {
            "decisionType": "DENY",
            "decisionId": decision_id,
            "allow": False,
            "reasonCode": "CARD_BLOCKED",
        }
        log_status = "DENY"
    elif card["cardStatus"] == "EXPIRED":
        decision = {
            "decisionType": "DENY",
            "decisionId": decision_id,
            "allow": False,
            "reasonCode": "CARD_EXPIRED",
        }
        log_status = "DENY"
    else:
        decision = {
            "decisionType": "ALLOW",
            "decisionId": decision_id,
            "allow": True,
            "policyId": "POLICY-01",
            "expiresAt": None,
        }
        log_status = "ALLOW"

    # Lưu decision
    DECISIONS.append({**decision, "cardId": payload.cardId, "gateId": payload.gateId})

    # Ghi access log
    ACCESS_LOGS.append({
        "logId": log_id,
        "cardId": payload.cardId,
        "gateId": payload.gateId,
        "direction": "IN",
        "status": log_status,
        "timestamp": timestamp,
        "operatorNote": None,
    })

    return decision


@app.get(
    "/decisions/{decisionId}",
    dependencies=[Depends(verify_bearer_token)],
    responses={404: {"model": ProblemDetails}},
)
def get_decision(decisionId: str) -> Dict:
    for item in DECISIONS:
        if item["decisionId"] == decisionId:
            return item

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=build_problem(
            status_code=status.HTTP_404_NOT_FOUND,
            title="Not Found",
            detail=f"Decision {decisionId} does not exist",
            instance=f"/decisions/{decisionId}",
            problem_type="https://smart-campus.local/problems/not-found",
        ),
    )


@app.get(
    "/policies/access/{policyId}",
    response_model=AccessPolicy,
    dependencies=[Depends(verify_bearer_token)],
    responses={404: {"model": ProblemDetails}},
)
def get_policy(policyId: str) -> AccessPolicy:
    policy = POLICIES.get(policyId)
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=build_problem(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Not Found",
                detail=f"Policy {policyId} does not exist",
                instance=f"/policies/access/{policyId}",
                problem_type="https://smart-campus.local/problems/not-found",
            ),
        )
    return AccessPolicy(**policy)


@app.get(
    "/access/logs/recent",
    response_model=List[AccessLog],
    dependencies=[Depends(verify_bearer_token)],
    responses={401: {"model": ProblemDetails}},
)
def get_recent_logs(
    limit: int = Query(default=10, ge=1, le=100),
) -> List[Dict]:
    return ACCESS_LOGS[-limit:]


@app.get(
    "/access/logs/{logId}",
    response_model=AccessLog,
    dependencies=[Depends(verify_bearer_token)],
    responses={404: {"model": ProblemDetails}},
)
def get_log_by_id(logId: str) -> Dict:
    for item in ACCESS_LOGS:
        if item["logId"] == logId:
            return item

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=build_problem(
            status_code=status.HTTP_404_NOT_FOUND,
            title="Not Found",
            detail=f"Access log {logId} does not exist",
            instance=f"/access/logs/{logId}",
            problem_type="https://smart-campus.local/problems/not-found",
        ),
    )


@app.get(
    "/gates/{gateId}/status",
    response_model=GateStatus,
    dependencies=[Depends(verify_bearer_token)],
    responses={404: {"model": ProblemDetails}},
)
def get_gate_status(gateId: str) -> GateStatus:
    gate = GATES.get(gateId)
    if not gate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=build_problem(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Not Found",
                detail=f"Gate {gateId} does not exist",
                instance=f"/gates/{gateId}/status",
                problem_type="https://smart-campus.local/problems/not-found",
            ),
        )
    return GateStatus(**gate)


@app.get(
    "/cards/{cardId}",
    response_model=CardInfo,
    dependencies=[Depends(verify_bearer_token)],
    responses={404: {"model": ProblemDetails}},
)
def get_card(cardId: str) -> CardInfo:
    card = CARDS.get(cardId)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=build_problem(
                status_code=status.HTTP_404_NOT_FOUND,
                title="Not Found",
                detail=f"Card {cardId} does not exist",
                instance=f"/cards/{cardId}",
                problem_type="https://smart-campus.local/problems/not-found",
            ),
        )
    return CardInfo(**card)