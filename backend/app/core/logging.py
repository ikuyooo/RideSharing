"""Logging setup with a location-privacy filter (Revision 9, Section 59.2).

Code must not log coordinates in the first place; this filter is a safety net
that masks any decimal number with 4+ fractional digits (lat/lon precision)
before a record is emitted.
"""

import logging
import re

_PRECISE_NUMBER = re.compile(r"-?\d{1,3}\.\d{4,}")
MASK = "<coord-redacted>"


class CoordinateRedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        redacted = _PRECISE_NUMBER.sub(MASK, message)
        if redacted != message:
            record.msg = redacted
            record.args = None
        return True


def configure_logging(level: str) -> None:
    logging.basicConfig(level=level)
    redaction = CoordinateRedactionFilter()
    for handler in logging.getLogger().handlers:
        handler.addFilter(redaction)
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        for handler in logging.getLogger(name).handlers:
            handler.addFilter(redaction)
