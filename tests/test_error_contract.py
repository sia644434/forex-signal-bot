from __future__ import annotations

import core.errors as errors


def test_application_error_preserves_message_and_details() -> None:
    error = errors.ApplicationError("failed", {"symbol": "EURUSD"})

    assert str(error) == "failed"
    assert error.message == "failed"
    assert error.details == {"symbol": "EURUSD"}


def test_application_error_defaults_details_to_empty_mapping() -> None:
    error = errors.ApplicationError("failed")

    assert error.details == {}


def test_domain_error_hierarchy_and_codes_are_stable() -> None:
    assert errors.ConfigurationError.code == "configuration_error"
    assert errors.CriticalServiceError.code == "critical_service_error"
    assert errors.ProviderTimeoutError.code == "provider_timeout"
    assert issubclass(errors.CriticalServiceError, errors.ServiceError)
    assert issubclass(errors.ProviderTimeoutError, errors.ProviderError)
    assert issubclass(errors.ProviderError, errors.DataError)
    assert issubclass(errors.DataError, errors.ApplicationError)


def test_handle_exception_logs_error_code_at_requested_level(monkeypatch) -> None:
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeLogger:
        def warning(self, *args: object) -> None:
            calls.append(("warning", args))

        def exception(self, *args: object) -> None:
            calls.append(("exception", args))

    monkeypatch.setattr(errors, "logger", FakeLogger())

    error = errors.ProviderTimeoutError("provider timed out")
    errors.handle_exception(error, level="warning")

    assert calls == [
        ("warning", ("%s: %s", "provider_timeout", error)),
    ]


def test_handle_exception_falls_back_to_exception_logger_for_unknown_level(monkeypatch) -> None:
    calls: list[tuple[str, tuple[object, ...]]] = []

    class FakeLogger:
        def exception(self, *args: object) -> None:
            calls.append(("exception", args))

    monkeypatch.setattr(errors, "logger", FakeLogger())

    error = errors.ApplicationError("unexpected")
    errors.handle_exception(error, level="not_a_logger_level")

    assert calls == [
        ("exception", ("%s: %s", "application_error", error)),
    ]
