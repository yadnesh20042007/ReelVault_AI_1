from functools import lru_cache
from urllib.parse import urlsplit, urlunsplit

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


_SUPABASE_SERVICE_PATHS = {
    "/auth/v1",
    "/functions/v1",
    "/realtime/v1",
    "/rest/v1",
    "/storage/v1",
}


from pathlib import Path

_SERVER_DIR = Path(__file__).resolve().parent.parent
_ENV_FILE = _SERVER_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(_ENV_FILE, ".env"), extra="ignore")

    app_env: str = "dev"
    cors_origins: list[str] | str = [
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:5174",
        "http://localhost:5174",
    ]

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""

    socialkit_api_key: str = ""
    socialkit_base_url: str = "https://api.socialkit.dev"
    tavily_api_key: str = ""
    gemini_api_key: str = ""
    gemini_api_key_2: str = ""
    gemini_api_key_3: str = ""
    gemini_api_keys: list[str] | str = []
    llm_model_fast: str = "gemini-3.5-flash-lite"
    llm_model_main: str = "gemini-3.5-flash-lite"
    # Fail fast per key so we can immediately rotate/fallback to the next
    # configured key when a quota limit or rate limit is reached.
    llm_max_retries: int = 0

    shallow_per_day: int = 50
    deep_per_day: int = 10
    verify_max_tool_calls: int = 6
    verify_timeout_s: int = 45
    research_max_tool_calls: int = 10
    research_timeout_s: int = 90
    stale_job_minutes: int = 15
    default_timezone: str = "Asia/Kolkata"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def normalize_cors_origins(cls, value: object) -> list[str]:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return ["*"]
            if value.startswith("[") and value.endswith("]"):
                try:
                    import json
                    parsed = json.loads(value)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except Exception:
                    pass
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return ["*"]

    @field_validator("supabase_url", mode="before")
    @classmethod
    def normalize_supabase_url(cls, value: object) -> object:
        """Accept the project URL even if a Supabase service endpoint was pasted."""
        if not isinstance(value, str):
            return value

        trimmed = value.strip()
        if not trimmed:
            return ""

        parsed = urlsplit(trimmed)
        if parsed.path.rstrip("/") not in _SUPABASE_SERVICE_PATHS:
            return trimmed.rstrip("/")

        # supabase-py appends service paths such as `/rest/v1` itself.
        return urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))

    def get_all_gemini_keys(self) -> list[str]:
        keys: list[str] = []
        if isinstance(self.gemini_api_keys, list):
            for k in self.gemini_api_keys:
                if isinstance(k, str) and k.strip():
                    keys.append(k.strip())
        elif isinstance(self.gemini_api_keys, str) and self.gemini_api_keys.strip():
            for k in self.gemini_api_keys.split(","):
                if k.strip():
                    keys.append(k.strip())

        for key_candidate in (self.gemini_api_key, self.gemini_api_key_2, self.gemini_api_key_3):
            if key_candidate and key_candidate.strip():
                for k in key_candidate.split(","):
                    if k.strip():
                        keys.append(k.strip())

        import os

        for env_k, env_v in os.environ.items():
            if env_k.startswith("GEMINI_API_KEY") and env_v.strip():
                for k in env_v.split(","):
                    if k.strip():
                        keys.append(k.strip())

        seen: set[str] = set()
        deduped: list[str] = []
        for k in keys:
            if k not in seen:
                seen.add(k)
                deduped.append(k)
        return deduped

    @model_validator(mode="after")
    def _sync_primary_gemini_key(self) -> "Settings":
        all_keys = self.get_all_gemini_keys()
        if all_keys and not self.gemini_api_key:
            self.gemini_api_key = all_keys[0]
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
