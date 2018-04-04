import yaml
import logging.config
import os

with open(os.getenv("P2K16_LOGGING")) as f:
    cfg = yaml.safe_load(f)

logging.config.dictConfig(cfg)

bind = "127.0.0.1:5000"
