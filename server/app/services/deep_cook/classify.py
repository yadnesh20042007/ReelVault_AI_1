from langchain_core.messages import HumanMessage, SystemMessage

from app.llm import get_llm
from app.schemas.domain import Classification, FetchedPost
from app.services.deep_cook import prompts as P


def classify(post: FetchedPost) -> Classification:
    llm = get_llm("fast").with_structured_output(Classification)
    user = (
        "Use the complete reel text below. Do not ignore either block.\n"
        + P.wrap("saved_title", (post.raw or {}).get("saved_title"))
        + "\n"
        + P.wrap("transcript", post.transcript)
        + "\n"
        + P.wrap("caption", post.caption)
    )
    return llm.invoke([SystemMessage(P.CLASSIFY_SYSTEM), HumanMessage(user)])
