from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class UserPublic(BaseModel):
    id: str
    name: str
    email: str
    plan: str = "free"
    created_at: datetime


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=40)
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=8, max_length=80)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        email = value.strip().lower()
        if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
            raise ValueError("Invalid email address.")
        return email

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        has_letter = any(char.isalpha() for char in value)
        has_digit = any(char.isdigit() for char in value)
        if not has_letter or not has_digit:
            raise ValueError("Password must include letters and numbers.")
        return value


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=8, max_length=80)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class AuthResponse(BaseModel):
    token: str
    user: UserPublic


class MessageResponse(BaseModel):
    message: str


class PlanInfo(BaseModel):
    id: str
    name: str
    price: str
    quota: int
    features: list[str]
    highlighted: bool = False


class CheckoutRequest(BaseModel):
    plan: str = Field(max_length=30)


class CheckoutResponse(BaseModel):
    status: str
    plan: str
    message: str
    checkout_url: str | None = None


class SuggestionSection(BaseModel):
    title: str
    items: list[str]


class AnalyzeRequest(BaseModel):
    candidate_name: str = Field(default="Anonymous Candidate", max_length=50)
    resume_text: str = Field(min_length=20, max_length=20000)
    job_description: str = Field(min_length=20, max_length=20000)
    target_role: str = Field(default="Target Role", max_length=80)
    provider: str = Field(default="auto", max_length=30)
    user_id: str | None = Field(default=None, max_length=80)


class MatchOverview(BaseModel):
    score: int
    matched_keywords: list[str]
    missing_keywords: list[str]
    resume_focus: list[str]


class ProviderMeta(BaseModel):
    model_config = {"protected_namespaces": ()}

    provider_used: str
    model_used: str | None = None
    fallback_used: bool = False
    llm_enabled: bool = False


class MetaResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    app_name: str
    version: str
    default_provider: str
    available_providers: list[str]
    llm_enabled: bool
    model_name: str | None = None
    cors_origins: list[str]


class AnalyzeResponse(BaseModel):
    id: str | None = None
    created_at: datetime | None = None
    candidate_name: str
    target_role: str
    provider_meta: ProviderMeta
    summary: str
    match_overview: MatchOverview
    strengths: list[str]
    risks: list[str]
    suggestion_sections: list[SuggestionSection]
    optimized_summary: str
    tailored_bullets: list[str]
    keyword_density: dict[str, int]
    report_markdown: str


class AnalysisHistoryItem(BaseModel):
    id: str
    created_at: datetime
    candidate_name: str
    target_role: str
    score: int
    provider_used: str
    summary: str


class AnalysisHistoryResponse(BaseModel):
    items: list[AnalysisHistoryItem]
