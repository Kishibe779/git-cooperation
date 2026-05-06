from __future__ import annotations

import hashlib
import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

from app.core.errors import AppError
from app.models.schemas import AnalyzeResponse, UserPublic


class JsonStore:
    def __init__(self) -> None:
        project_root = Path(__file__).resolve().parents[3]
        self.path = Path(os.getenv("APP_STORE_PATH", project_root / ".runtime" / "app_store.json"))
        self.lock = RLock()

    def ensure_ready(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({"users": [], "sessions": {}, "analyses": []})

    def register(self, name: str, email: str, password: str) -> tuple[str, UserPublic]:
        email_key = email.strip().lower()
        with self.lock:
            data = self._read_unlocked()
            if any(user["email"] == email_key for user in data["users"]):
                raise AppError("This email is already registered.", status_code=409, code="email_exists")
            user = {
                "id": secrets.token_urlsafe(12),
                "name": name.strip(),
                "email": email_key,
                "password_hash": self._hash_password(password),
                "plan": "free",
                "created_at": self._now(),
            }
            token = secrets.token_urlsafe(32)
            data["users"].append(user)
            data["sessions"][token] = user["id"]
            self._write(data)
            return token, self._public_user(user)

    def login(self, email: str, password: str) -> tuple[str, UserPublic]:
        email_key = email.strip().lower()
        with self.lock:
            data = self._read_unlocked()
            user = next((item for item in data["users"] if item["email"] == email_key), None)
            if not user or user["password_hash"] != self._hash_password(password):
                raise AppError("Invalid email or password.", status_code=401, code="invalid_credentials")
            token = secrets.token_urlsafe(32)
            data["sessions"][token] = user["id"]
            self._write(data)
            return token, self._public_user(user)

    def get_user_by_token(self, token: str | None) -> UserPublic:
        if not token:
            raise AppError("Authentication is required.", status_code=401, code="auth_required")
        with self.lock:
            data = self._read_unlocked()
            user_id = data["sessions"].get(token)
            user = next((item for item in data["users"] if item["id"] == user_id), None)
        if not user:
            raise AppError("Session expired. Please sign in again.", status_code=401, code="invalid_session")
        return self._public_user(user)

    def logout(self, token: str | None) -> None:
        if not token:
            return
        with self.lock:
            data = self._read_unlocked()
            data["sessions"].pop(token, None)
            self._write(data)

    def update_plan(self, user_id: str, plan: str) -> UserPublic:
        with self.lock:
            data = self._read_unlocked()
            user = next((item for item in data["users"] if item["id"] == user_id), None)
            if not user:
                raise AppError("User not found.", status_code=404, code="user_not_found")
            user["plan"] = plan
            self._write(data)
            return self._public_user(user)

    def save_analysis(self, user_id: str | None, result: AnalyzeResponse) -> AnalyzeResponse:
        if not user_id:
            return result
        with self.lock:
            data = self._read_unlocked()
            analysis_id = secrets.token_urlsafe(10)
            created_at = self._now()
            result.id = analysis_id
            result.created_at = datetime.fromisoformat(created_at)
            data["analyses"].insert(
                0,
                {
                    "id": analysis_id,
                    "user_id": user_id,
                    "created_at": created_at,
                    "candidate_name": result.candidate_name,
                    "target_role": result.target_role,
                    "score": result.match_overview.score,
                    "provider_used": result.provider_meta.provider_used,
                    "summary": result.summary,
                    "payload": result.model_dump(mode="json"),
                },
            )
            data["analyses"] = data["analyses"][:200]
            self._write(data)
            return result

    def list_analyses(self, user_id: str) -> list[dict[str, Any]]:
        with self.lock:
            data = self._read_unlocked()
            items = [
                {
                    "id": item["id"],
                    "created_at": item["created_at"],
                    "candidate_name": item["candidate_name"],
                    "target_role": item["target_role"],
                    "score": item["score"],
                    "provider_used": item["provider_used"],
                    "summary": item["summary"],
                }
                for item in data["analyses"]
                if item["user_id"] == user_id
            ]
        return items[:30]

    def _read_unlocked(self) -> dict[str, Any]:
        self.ensure_ready()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {"users": [], "sessions": {}, "analyses": []}
            self._write(data)
        data.setdefault("users", [])
        data.setdefault("sessions", {})
        data.setdefault("analyses", [])
        return data

    def _write(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        temp_path.replace(self.path)

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(f"resume-optimizer::{password}".encode("utf-8")).hexdigest()

    def _public_user(self, user: dict[str, Any]) -> UserPublic:
        return UserPublic(
            id=user["id"],
            name=user["name"],
            email=user["email"],
            plan=user.get("plan", "free"),
            created_at=datetime.fromisoformat(user["created_at"]),
        )

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()


store = JsonStore()
