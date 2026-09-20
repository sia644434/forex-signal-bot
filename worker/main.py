from __future__ import annotations

import signal
import time

from core.logger import setup_logger
from config.settings import Settings
from .executors import register_real_executors
from .handlers import register_default_handlers
from .runtime import WorkerRuntime
from .server import WorkerHTTPServer


logger = setup_logger()
settings = Settings.load()


def main() -> None:
    runtime = WorkerRuntime.create()
    register_default_handlers(runtime)
    register_real_executors(runtime)

    server = WorkerHTTPServer(runtime)
    server.start()
    logger.info(
        "PC Worker %s ready on %s:%s",
        runtime.worker_id,
        server.host,
        server.port,
    )
    stop = False

    def shutdown(*_args):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    while not stop:
        time.sleep(1)
    server.stop()


if __name__ == "__main__":
    main()
