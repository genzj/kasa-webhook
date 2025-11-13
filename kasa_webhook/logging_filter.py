import logging

L = logging.getLogger(__name__)


class AccessPathFilter(logging.Filter):
    """Filter to exclude Uvicorn access logs for specific paths."""

    def __init__(self, excluded_paths: list[str], name=""):
        super().__init__(name)
        L.info(f"{excluded_paths=!r}")
        self.excluded_paths = set(p.strip() for p in excluded_paths)

    def filter(self, record: logging.LogRecord) -> bool:
        if record.args and len(record.args) >= 3:
            request_path = record.args[2]  # type: ignore[index]
            # Return False to suppress the log record
            return (
                not isinstance(request_path, str)
                or request_path not in self.excluded_paths
            )
        return True
