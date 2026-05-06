from fastapi import APIRouter, Header

from app.core.errors import AppError
from app.models.schemas import (
    AnalysisHistoryItem,
    AnalysisHistoryResponse,
    AuthResponse,
    CheckoutRequest,
    CheckoutResponse,
    LoginRequest,
    MessageResponse,
    PlanInfo,
    RegisterRequest,
    UserPublic,
)
from app.services.store import store

router = APIRouter(tags=["users"])

PLANS = [
    PlanInfo(
        id="free",
        name="Free",
        price="CNY 0 / month",
        quota=5,
        features=[
            "Rule-based resume matching",
            "Markdown report export",
            "Save up to 30 analysis records",
        ],
    ),
    PlanInfo(
        id="pro",
        name="Pro",
        price="CNY 29 / month",
        quota=80,
        features=[
            "DeepSeek priority analysis",
            "Longer rewrite suggestions",
            "Application planning and saved reports",
        ],
        highlighted=True,
    ),
    PlanInfo(
        id="team",
        name="Team",
        price="CNY 99 / month",
        quota=400,
        features=[
            "Shared team quota",
            "Role templates for teams",
            "Interview prep and resume version management",
        ],
    ),
]


@router.post("/auth/register", response_model=AuthResponse)
def register(payload: RegisterRequest) -> AuthResponse:
    token, user = store.register(payload.name, payload.email, payload.password)
    return AuthResponse(token=token, user=user)


@router.post("/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    token, user = store.login(payload.email, payload.password)
    return AuthResponse(token=token, user=user)


@router.get("/auth/me", response_model=UserPublic)
def me(authorization: str | None = Header(default=None)) -> UserPublic:
    return _current_user(authorization)


@router.post("/auth/logout", response_model=MessageResponse)
def logout(authorization: str | None = Header(default=None)) -> MessageResponse:
    token = _bearer_token(authorization)
    store.logout(token)
    return MessageResponse(message="Signed out.")


@router.get("/plans", response_model=list[PlanInfo])
def plans() -> list[PlanInfo]:
    return PLANS


@router.post("/billing/checkout", response_model=CheckoutResponse)
def checkout(payload: CheckoutRequest, authorization: str | None = Header(default=None)) -> CheckoutResponse:
    user = _current_user(authorization)
    plan_ids = {plan.id for plan in PLANS}
    if payload.plan not in plan_ids:
        raise AppError("Unknown plan.", status_code=400, code="invalid_plan")
    updated = store.update_plan(user.id, payload.plan)
    return CheckoutResponse(
        status="activated",
        plan=updated.plan,
        message=(
            "Demo checkout completed. In production this endpoint can connect "
            "to Stripe, Alipay, or WeChat Pay."
        ),
        checkout_url=None,
    )


@router.get("/analyses", response_model=AnalysisHistoryResponse)
def history(authorization: str | None = Header(default=None)) -> AnalysisHistoryResponse:
    user = _current_user(authorization)
    return AnalysisHistoryResponse(items=[AnalysisHistoryItem(**item) for item in store.list_analyses(user.id)])


def _current_user(authorization: str | None) -> UserPublic:
    return store.get_user_by_token(_bearer_token(authorization))


def _bearer_token(authorization: str | None) -> str | None:
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    return token
