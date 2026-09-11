# app/data_runtime/exceptions.py


class DataRuntimeError(Exception):
    """Base exception for the data runtime."""


class DataSourceError(DataRuntimeError):
    """Raised when a data source cannot be loaded."""


class QueryError(DataRuntimeError):
    """Raised when a query cannot be executed."""


class QueryValidationError(DataRuntimeError):
    """Raised when a query violates runtime safety rules."""


class DatasetNotFoundError(DataRuntimeError):
    """Raised when a dataset does not exist."""


class UnsupportedFileTypeError(DataRuntimeError):
    """Raised for unsupported file formats."""


class ResourceLimitError(DataRuntimeError):
    """Raised when a runtime resource limit is exceeded."""
