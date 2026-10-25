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


SURVEY_PATH_PREFIXES = ("/survey/", "/api/survey/")


class SurveyClientAddressFilter(logging.Filter):
    """Survey respondents are anonymous (Section 59.2): drop the client address
    from uvicorn access-log records of survey paths. uvicorn.access records
    carry args (client_addr, method, path, http_version, status)."""

    def filter(self, record: logging.LogRecord) -> bool:
        args = record.args
        if isinstance(args, tuple) and len(args) >= 3 and isinstance(args[2], str) \
                and args[2].startswith(SURVEY_PATH_PREFIXES):
            record.args = ("-", *args[1:])
        return True


def configure_logging(level: str) -> None:
    logging.basicConfig(level=level)
    redaction = CoordinateRedactionFilter()
    for handler in logging.getLogger().handlers:
        handler.addFilter(redaction)
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        for handler in logging.getLogger(name).handlers:
            handler.addFilter(redaction)
    # Logger-level filter so it applies whatever handlers uvicorn installs later.
    logging.getLogger("uvicorn.access").addFilter(SurveyClientAddressFilter())
