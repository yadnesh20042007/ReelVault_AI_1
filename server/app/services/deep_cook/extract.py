import logging

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import ValidationError

from app.config import get_settings
from app.llm import get_llm
from app.schemas.domain import Extracted, FetchedPost
from app.services.deep_cook import prompts as P

log = logging.getLogger("deep_cook.extract")


def extract(post: FetchedPost) -> Extracted:
    llm = get_llm("main").with_structured_output(Extracted)
    system = P.EXTRACT_SYSTEM.replace("{tz}", get_settings().default_timezone)
    user = (
        "Extract from the complete reel text below.\n"
        f"posted_at: {post.posted_at.isoformat() if post.posted_at else 'unknown'}\n"
        + P.wrap("transcript", post.transcript)
        + "\n"
        + P.wrap("caption", post.caption)
    )
    result = llm.invoke([SystemMessage(system), HumanMessage(user)])
    if isinstance(result, Extracted):
        return result
    if isinstance(result, dict):
        try:
            return Extracted.model_validate(result)
        except ValidationError:
            log.warning("extractor returned an invalid structured result; using an empty extraction")
            return Extracted()

    # A provider can return an empty parsed result even when the HTTP request
    # succeeded. Keep the reel usable and let the pipeline finish with the
    # explicit "not enough details" result instead of crashing on None.title.
    log.warning("extractor returned no structured result; using an empty extraction")
    return Extracted()
