FROM python:3.6-onbuild

ENV FLASK_APP p2k16.web.server
ENV P2K16_CONFIG /usr/src/app/config-local.cfg
ENV PYTHONPATH /usr/src/app

RUN curl -sL https://deb.nodesource.com/setup_4.x | bash -
RUN apt-get update && apt-get install -y nodejs build-essential && apt-get clean

RUN npm install -g bower
RUN bower --allow-root install

EXPOSE 5000
CMD flask run --host=0.0.0.0