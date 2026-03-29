"""SSE stream formatting utilities.

Converts SSEEvent objects into EventSource wire format (text/event-stream).
The wire format follows the W3C EventSource specification:
  https://html.spec.whatwg.org/multipage/server-sent-events.html

Each event is serialised as:
    event: <type>\\n
    data: <json>\\n
    \\n
"""

import json
import logging
from collections.abc import AsyncIterator

from api.sse.events import ErrorPayload, SSEEvent, SSEEventType

logger = logging.getLogger(__name__)


def format_sse_event(event: SSEEvent) -> str:
    """Format an SSEEvent as EventSource wire text.

    Produces the standard two-line form required by the EventSource spec:
        event: <type>\\n
        data: <json>\\n
        \\n

    Args:
        event: The SSEEvent to serialise.

    Returns:
        String in format ``"event: {type}\\ndata: {json}\\n\\n"``.
    """
    event_line = f"event: {event.event}"
    data_line = f"data: {json.dumps(event.data, ensure_ascii=False)}"
    return f"{event_line}\n{data_line}\n\n"


async def sse_response_generator(
    events: AsyncIterator[SSEEvent],
) -> AsyncIterator[str]:
    """Async generator that formats SSEEvents for StreamingResponse.

    Iterates the source ``events`` iterator, formats each event to wire
    format, and yields the resulting strings.  If the source iterator raises
    an exception the generator catches it, emits a terminal ERROR event, and
    then stops — so the client always receives a clean terminal signal.

    Args:
        events: An async iterator of SSEEvent objects from the pipeline.

    Yields:
        Formatted SSE strings suitable for use with FastAPI StreamingResponse
        (``media_type="text/event-stream"``).
    """
    try:
        async for event in events:
            yield format_sse_event(event)
    except Exception as exc:
        logger.exception("SSE source iterator raised an unhandled exception: %s", exc)
        error_event = SSEEvent(
            event=SSEEventType.ERROR,
            data=ErrorPayload(
                job_id=None,
                code="STREAM_ERROR",
                message=str(exc),
                stage=None,
            ).model_dump(),
        )
        yield format_sse_event(error_event)
