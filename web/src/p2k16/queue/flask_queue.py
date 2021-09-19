import logging
import threading
import flask

from . import *

logger = logging.getLogger(__name__)


def make_thread(config: QueueConfig, app: flask.Flask, db):
    def runner():
        logger.info("Queue thread started")
        with app.app_context():
            queue = QueueConsumer(config, db.engine)
            queue.run()

    return threading.Thread(target=runner, name=f"Q-{config.name}", daemon=True)
