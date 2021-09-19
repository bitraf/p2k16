import datetime
import logging
import select
import time
import typing
from typing import Optional, Callable

from sqlalchemy.engine.base import Connection
from . import sql

logger = logging.getLogger(__name__)

__all__ = [
    'QueueConsumer',
    'QueueConfig',
    'Message',
    'ConnectionProvider',
]


class Message:
    def __init__(self, _id: int, created_at: datetime, processed_at: datetime, queue: str, entity_id: int):
        self.id = _id
        self.created_at = created_at
        self.processed_at = processed_at
        self.queue = queue
        self.entity_id = entity_id


class QueueConfig:
    def __init__(self, name: str, handler: Callable[[Message], typing.Any]):
        self.name = name
        self.handler = handler


class ConnectionProvider:
    def connect(self) -> Connection:
        pass


def _pass():
    pass


class QueueConsumer:
    def __init__(self, config: QueueConfig, db: ConnectionProvider):
        self.config = config
        self.db = db
        self.con = None  # type: Optional[Connection]

    @staticmethod
    def find_unprocessed_messages(con, message_ids, limit: Optional[int] = None) -> typing.List[Message]:
        c = con.cursor()
        q = "SELECT id, created_at, processed_at, queue, entity_id " \
            "FROM q_message " \
            "WHERE processed_at IS NULL AND id = ANY(%s) " \
            "FOR UPDATE " \
            "SKIP LOCKED"

        if limit is not None:
            q += f" LIMIT {limit}"

        c.execute(q, [message_ids])
        messages = [Message(t[0], t[1], t[2], t[3], t[4]) for t in c.fetchall()]
        c.close()

        return messages

    def close(self):
        c = self.con
        if c is not None:
            c.close()

    def run(self):
        while self.run:
            with self.db.connect() as con:
                try:
                    self.con = con
                    self.with_connection()
                except Exception as e:
                    if not self.run:
                        # Ignore exceptions when shutting down, most likely the connection has been closed
                        pass
                    logger.warning("Handler failed", exc_info=e)
                    time.sleep(1)
                finally:
                    self.con = None

    def with_connection(self):
        logger.info("Waiting for notifications")
        self.con.execution_options(isolation_level="AUTOCOMMIT")
        self.con.detach()
        underlying = self.con.connection.connection
        underlying.autocommit = True
        logger.info(f"ret={underlying}")

        c = underlying.cursor()
        logger.info(f"c={c}")
        c.execute(f'listen "{self.config.name}";')
        # c.close()
        logger.info(f"ret={underlying}")

        while True:
            r, w, x = select.select([underlying], [], [], 60)

            if (r, w, x) == ([], [], []):
                # logger.info("timeout")
                # underlying.poll()
                # logger.info(f"notifies={underlying.notifies}")
                continue

            underlying.poll()
            logger.info(f"notifies={underlying.notifies}")

            payloads = [int(n.payload) for n in underlying.notifies]
            underlying.notifies = []

            self.process_messages(payloads)

            time.sleep(1)

    def process_messages(self, payloads):
        with self.db.connect() as con:
            tx = con.begin()
            try:
                underlying = con.connection.connection

                messages = self.find_unprocessed_messages(underlying, payloads)

                for m in messages:
                    logger.info(f"Processing: queue={m.queue}, id={m.id}, entity_id={m.entity_id}")
                    _id = m.id
                    self.config.handler(m)
                    sql.set_processed(underlying, _id)
                tx.commit()
                tx = None
            finally:
                try:
                    if tx is not None:
                        tx.rollback()
                except Exception as e:
                    logger.warning("Exception while rolling back transaction", exc_info=e)
