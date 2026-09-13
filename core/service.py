from __future__ import annotations

from services.base import BaseService

from core.errors import CriticalServiceError, handle_exception
from core.logger import setup_logger


logger = setup_logger()


class ServiceManager:
    """Register, start, stop and health-check application services."""

    def __init__(self) -> None:
        self.services: dict[str, BaseService] = {}
        self._started_services: list[BaseService] = []

    def register(self, service: BaseService) -> None:
        if service.name in self.services:
            raise ValueError(f"Service already registered: {service.name}")
        self.services[service.name] = service

    async def start_all(self) -> None:
        for service in self.services.values():
            try:
                result = service.start()
                if hasattr(result, "__await__"):
                    await result
                self._started_services.append(service)
                logger.info("%s service started.", service.name)
            except Exception as error:
                handle_exception(error)
                # Keep the failed service in the lifecycle tracking set until its
                # cleanup succeeds. A partial start can allocate resources before
                # raising, and a failed cleanup must remain retryable by stop_all().
                previously_started = list(self._started_services)
                if service not in self._started_services:
                    self._started_services.append(service)
                await self._stop_services([service])
                if service.critical:
                    await self._stop_services(previously_started)
                    raise CriticalServiceError(
                        f"Critical service failed to start: {service.name}",
                        {"service": service.name},
                    ) from error
                logger.warning(
                    "%s service failed to start; continuing in degraded mode.",
                    service.name,
                )

    async def stop_all(self) -> None:
        await self._stop_services(list(self._started_services))

    async def _stop_services(self, services: list[BaseService]) -> None:
        for service in reversed(services):
            try:
                result = service.stop()
                if hasattr(result, "__await__"):
                    await result
                if service in self._started_services:
                    self._started_services.remove(service)
                logger.info("%s service stopped.", service.name)
            except Exception as error:
                handle_exception(error)

    def health(self) -> dict:
        result = {}
        for name, service in self.services.items():
            try:
                result[name] = service.health()
            except Exception as error:
                handle_exception(error)
                result[name] = {
                    "service": name,
                    "status": "error",
                    "critical": service.critical,
                }
        return result
