from app.jobs.queue import ReceivedMessage


class InMemoryJobQueue:
    """Fila em memoria para testes. receive nao remove; delete sim."""

    def __init__(self) -> None:
        self.pending: list[tuple[str, str]] = []
        self.deleted: list[str] = []
        self._n = 0

    def send(self, body: str) -> None:
        self._n += 1
        self.pending.append((str(self._n), body))

    def receive(self) -> ReceivedMessage | None:
        if not self.pending:
            return None
        handle, body = self.pending[0]
        return ReceivedMessage(receipt_handle=handle, body=body)

    def delete(self, receipt_handle: str) -> None:
        self.deleted.append(receipt_handle)
        self.pending = [(handle, body) for handle, body in self.pending if handle != receipt_handle]
