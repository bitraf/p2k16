FROM python:3.6-onbuild

ENV FLASK_APP p2k16_web/server.py
ENV P2K16_CONFIG /usr/src/app/config-local.cfg
ENV PYTHONPATH /usr/src/app

EXPOSE 5000
CMD flask run --host=0.0.0.0