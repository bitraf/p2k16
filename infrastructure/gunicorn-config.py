import yaml
import logging.config
import os

with open(os.getenv("P2K16_LOGGING")) as f:
    cfg = yaml.safe_load(f)

logging.config.dictConfig(cfg)

if not os.path.isdir("log"):
    os.mkdir("log")

accesslog = "log/access.log"

bind = "127.0.0.1:5000"

pidfile = "p2k16.pid"

timeout = 5 * 60
