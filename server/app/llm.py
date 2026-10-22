import json
import logging
import os
import re
import threading
import time
from typing import Any, Literal, Optional

from google.api_core.exceptions import ResourceExhausted, TooManyRequests
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, Generation
from langchain_core.output_parsers import BaseOutputParser
from langchain_core.runnables import Runnable
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from pydantic import BaseModel

from app.config import get_settings
from app.errors import PipelineError

log = logging.getLogger("llm")


def _mask_key(key: str) -> str:
    if len(key) <= 8:
        return "***"
    return f"{key[:4]}...{key[-4:]}"


class ModelQuotaError(ResourceExhausted):
    """Raised when a specific model encounters quota exhaustion or rate limits."""

    def __init__(self, model_name: str, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.model_name = model_name
        self.retry_after = retry_after


class AllModelsExhaustedError(ResourceExhausted):
    """Raised when all configured primary and fallback models are quota-exhausted."""

    def __init__(self, message: str, exhausted_models: list[str]):
        super().__init__(message)
        self.exhausted_models = exhausted_models


def is_quota_or_rate_limit_error(exc: Exception) -> bool:
    """Strictly detect genuine 429 quota exhaustion or rate limits from Gemini / LangChain."""
    if isinstance(exc, (ResourceExhausted, TooManyRequests, ModelQuotaError, AllModelsExhaustedError)):
        return True
    msg = str(exc).lower()

    # Exclude non-quota errors immediately
    if any(
        k in msg
        for k in (
            "unauthenticated",
            "invalid api key",
            "api_key_invalid",
            "permission_denied",
            "permissiondenied",
            "invalid argument",
            "invalidargument",
            "is not found for api version",
            "model not found",
        )
    ):
        return False

    return any(
        needle in msg
        for needle in (
            "429",
            "resource_exhausted",
            "resourceexhausted",
            "quota",
            "rate limit",
            "rate_limit",
            "too many requests",
            "exceeded your current quota",
            "check quota",
        )
    )


def is_auth_error(exc: Exception) -> bool:
    """Detect invalid API keys or unauthenticated access (401/403)."""
    msg = str(exc).lower()
    return any(
        needle in msg
        for needle in (
            "api_key_invalid",
            "unauthenticated",
            "invalid api key",
            "permission_denied",
            "permissiondenied",
            "401",
            "403",
        )
    )


def is_not_found_error(exc: Exception) -> bool:
    """Detect unsupported or non-existent model identifiers (404)."""
    msg = str(exc).lower()
    return any(
        needle in msg
        for needle in (
            "404",
            "not_found",
            "not found",
            "is not found for api version",
            "model not found",
        )
    )


def is_invalid_argument_error(exc: Exception) -> bool:
    """Detect bad requests or malformed parameters (400)."""
    msg = str(exc).lower()
    return any(
        needle in msg
        for needle in (
            "400",
            "invalid_argument",
            "invalid argument",
            "bad request",
        )
    )


def parse_retry_after(exc: Exception) -> float | None:
    """Extract retry-after cooldown duration from exception headers or message."""
    resp = getattr(exc, "response", None)
    if resp and hasattr(resp, "headers"):
        retry_hdr = resp.headers.get("Retry-After") or resp.headers.get("retry-after")
        if retry_hdr:
            try:
                val = float(retry_hdr)
                if val > 0:
                    return min(max(val, 5.0), 86400.0)
            except (ValueError, TypeError):
                pass

    msg = str(exc)
    m = re.search(r"retry\s+(?:in|after)[:\s]+(\d+(?:\.\d+)?)\s*s?", msg, re.IGNORECASE)
    if m:
        try:
            val = float(m.group(1))
            if val > 0:
                return min(max(val, 5.0), 86400.0)
        except (ValueError, TypeError):
            pass

    msg_lower = msg.lower()
    if any(k in msg_lower for k in ("per day", "daily", "day quota", "rpd")):
        return 1800.0  # 30-minute cooldown for daily limit exhaustion
    if any(k in msg_lower for k in ("per minute", "rpm", "minute quota")):
        return 60.0  # 1-minute cooldown for RPM rate limit

    return None


class KeyPool:
    """Manages round-robin rotation and cooldown failover across Gemini API keys."""

    def __init__(self, cooldown_seconds: float = 300.0):
        self.cooldown_seconds = cooldown_seconds
        self._exhausted_until: dict[str, float] = {}
        self._lock = threading.Lock()
        self._rr_index: int = 0

    def mark_exhausted(self, key: str, duration: float | None = None) -> None:
        if not key:
            return
        duration = duration if duration is not None else self.cooldown_seconds
        with self._lock:
            self._exhausted_until[key] = time.time() + duration
            log.warning(
                "Gemini API key %s marked exhausted/rate-limited for %ds; failing over to other available keys.",
                _mask_key(key),
                int(duration),
            )

    def get_ordered_keys(self, all_keys: list[str]) -> list[str]:
        if not all_keys:
            return []
        if len(all_keys) == 1:
            return all_keys

        now = time.time()
        with self._lock:
            healthy = [k for k in all_keys if now >= self._exhausted_until.get(k, 0)]
            exhausted = [k for k in all_keys if now < self._exhausted_until.get(k, 0)]
            exhausted.sort(key=lambda k: self._exhausted_until.get(k, 0))

            if healthy:
                idx = self._rr_index % len(healthy)
                self._rr_index += 1
                rotated = healthy[idx:] + healthy[:idx]
                return rotated + exhausted
            return exhausted

    def reset(self) -> None:
        with self._lock:
            self._exhausted_until.clear()
            self._rr_index = 0


class ModelPool:
    """Tracks health, exhaustion cooldowns, and fallback priority across Gemini models."""

    def __init__(self, default_cooldown_seconds: float = 60.0):
        self.default_cooldown_seconds = default_cooldown_seconds
        self._exhausted_until: dict[str, float] = {}
        self._lock = threading.Lock()

    def mark_exhausted(self, model_name: str, duration: float | None = None) -> None:
        if not model_name:
            return
        dur = duration if duration is not None else self.default_cooldown_seconds
        with self._lock:
            self._exhausted_until[model_name] = time.time() + dur
            log.warning(
                "Gemini model '%s' marked exhausted/rate-limited for %ds; failing over to fallback models.",
                model_name,
                int(dur),
            )

    def is_exhausted(self, model_name: str) -> bool:
        with self._lock:
            return time.time() < self._exhausted_until.get(model_name, 0)

    def get_ordered_models(self, all_models: list[str]) -> list[str]:
        if not all_models:
            return []
        if len(all_models) == 1:
            return all_models

        now = time.time()
        with self._lock:
            healthy = [m for m in all_models if now >= self._exhausted_until.get(m, 0)]
            exhausted = [m for m in all_models if now < self._exhausted_until.get(m, 0)]
            exhausted.sort(key=lambda m: self._exhausted_until.get(m, 0))

            if healthy:
                return healthy + exhausted
            return exhausted

    def reset(self) -> None:
        with self._lock:
            self._exhausted_until.clear()


_key_pool = KeyPool()
_model_pool = ModelPool()
_is_key_or_quota_error = is_quota_or_rate_limit_error


class RobustModelOutputParser(BaseOutputParser):
    schema_cls: Any

    def parse_result(self, result: list[Generation], *, partial: bool = False) -> Any:
        if not result:
            return None
        gen = result[0]
        msg = getattr(gen, "message", None)

        # 1. Tool calls
        tool_calls = getattr(msg, "tool_calls", None) if msg else None
        if tool_calls and isinstance(tool_calls, list) and len(tool_calls) > 0:
            tc = tool_calls[0]
            args = tc.get("args") if isinstance(tc, dict) else getattr(tc, "args", None)
            if isinstance(args, dict):
                if isinstance(self.schema_cls, type) and issubclass(self.schema_cls, BaseModel):
                    return self.schema_cls.model_validate(args)
                return args
            elif isinstance(args, str) and args.strip():
                try:
                    data = json.loads(args)
                    if isinstance(self.schema_cls, type) and issubclass(self.schema_cls, BaseModel):
                        return self.schema_cls.model_validate(data)
                    return data
                except Exception:
                    pass

        # 2. Content text
        content = getattr(msg, "content", "") if msg else getattr(gen, "text", "")
        if isinstance(content, list):
            parts = []
            for p in content:
                if isinstance(p, str):
                    parts.append(p)
                elif isinstance(p, dict) and "text" in p:
                    parts.append(p["text"])
            content = "\n".join(parts)

        if not isinstance(content, str) or not content.strip():
            return None

        cleaned = content.strip()
        if "```" in cleaned:
            m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
            if m:
                cleaned = m.group(1).strip()

        try:
            data = json.loads(cleaned)
        except Exception:
            m = re.search(r"(\{[\s\S]*\})", cleaned)
            if m:
                data = json.loads(m.group(1))
            else:
                raise

        if isinstance(self.schema_cls, type) and issubclass(self.schema_cls, BaseModel):
            return self.schema_cls.model_validate(data)
        return data

    def parse(self, text: str) -> Any:
        return self.parse_result([ChatGeneration(message=AIMessage(content=text))])


class MonitoredChatGoogleGenerativeAI(ChatGoogleGenerativeAI):
    """ChatGoogleGenerativeAI that intercepts quota / rate limit errors to mark the model and key."""

    api_key_str: str = ""
    model_name_str: str = ""

    def _handle_exception(self, exc: Exception) -> None:
        if is_quota_or_rate_limit_error(exc):
            cooldown = parse_retry_after(exc)
            _model_pool.mark_exhausted(self.model_name_str, duration=cooldown)
            _key_pool.mark_exhausted(self.api_key_str, duration=cooldown)
            raise ModelQuotaError(
                model_name=self.model_name_str,
                message=f"Gemini model '{self.model_name_str}' quota or rate limit exceeded: {exc}",
                retry_after=cooldown,
            ) from exc

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        try:
            return super()._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
        except Exception as exc:
            self._handle_exception(exc)
            raise

    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        try:
            return await super()._agenerate(messages, stop=stop, run_manager=run_manager, **kwargs)
        except Exception as exc:
            self._handle_exception(exc)
            raise

    def with_structured_output(
        self,
        schema: Any,
        method: Optional[Literal["function_calling", "json_mode"]] = "json_mode",
        *,
        include_raw: bool = False,
        **kwargs: Any,
    ) -> Runnable:
        if method == "function_calling":
            return super().with_structured_output(schema, method="function_calling", include_raw=include_raw, **kwargs)

        schema_json = None
        if isinstance(schema, type) and issubclass(schema, BaseModel):
            from langchain_google_genai._function_utils import replace_defs_in_schema
            schema_json = replace_defs_in_schema(schema.model_json_schema())
        elif isinstance(schema, dict):
            schema_json = schema

        bind_kwargs: dict[str, Any] = {"response_mime_type": "application/json"}
        if schema_json:
            bind_kwargs["response_schema"] = schema_json

        parser = RobustModelOutputParser(schema_cls=schema)
        bound = self.bind(**bind_kwargs)
        if include_raw:
            from operator import itemgetter
            from langchain_core.runnables import RunnablePassthrough
            return {"raw": bound} | RunnablePassthrough.assign(
                parsed=itemgetter("raw") | parser
            )
        return bound | parser


def _build_model(model_name: str, key: str, max_retries: int, timeout: float = 30.0):
    # If using Google Gemini model
    if ":" not in model_name or model_name.startswith("google_genai:"):
        clean_model = model_name.split(":", 1)[1] if ":" in model_name else model_name
        return MonitoredChatGoogleGenerativeAI(
            model=clean_model,
            api_key=key,
            api_key_str=key,
            model_name_str=clean_model,
            temperature=0,
            max_retries=max_retries,
            timeout=timeout,
        )
    return init_chat_model(
        model_name,
        api_key=key,
        temperature=0,
        max_retries=max_retries,
        timeout=timeout,
    )


def get_llm(kind: Literal["fast", "main"] = "main", timeout: float | None = None):
    s = get_settings()
    keys = s.get_all_gemini_keys()
    if not keys:
        raise PipelineError("llm_unconfigured")

    ordered_keys = _key_pool.get_ordered_keys(keys)
    primary_key = ordered_keys[0]
    fallback_keys = ordered_keys[1:]

    os.environ.setdefault("GOOGLE_API_KEY", primary_key)
    primary_model = s.llm_model_fast if kind == "fast" else s.llm_model_main
    fallback_models = s.get_llm_fallback_models()
    all_candidate_models = [primary_model] + [m for m in fallback_models if m != primary_model]

    # Order models: healthy models first, exhausted models in cooldown at the end
    ordered_models = _model_pool.get_ordered_models(all_candidate_models)
    selected_primary_model = ordered_models[0]
    http_timeout = timeout if timeout is not None else getattr(s, "gemini_http_timeout_s", 30.0)

    primary = _build_model(
        selected_primary_model, primary_key, s.llm_max_retries, timeout=http_timeout
    )

    fallbacks = []
    # 1. Other models with primary key (highest priority fallback)
    for m in ordered_models[1:]:
        fallbacks.append(
            _build_model(m, primary_key, s.llm_max_retries, timeout=http_timeout)
        )
    # 2. All models with remaining keys if multiple keys configured
    for k in fallback_keys:
        for m in ordered_models:
            fallbacks.append(
                _build_model(m, k, s.llm_max_retries, timeout=http_timeout)
            )

    if not fallbacks:
        return primary

    return primary.with_fallbacks(
        fallbacks,
        exceptions_to_handle=(ModelQuotaError, ResourceExhausted, TooManyRequests),
    )
