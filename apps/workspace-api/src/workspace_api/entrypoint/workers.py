import threading

from workspace_api.application.order_worker import OrderWorker


def start_workers(worker: OrderWorker, count: int, idle_seconds: float = 1.0) -> threading.Event:
    stop = threading.Event()

    def loop() -> None:
        while not stop.is_set():
            if not worker.run_once():
                stop.wait(idle_seconds)

    for _ in range(count):
        threading.Thread(target=loop, daemon=True).start()
    return stop
