FROM python:3.5.1-alpine

RUN mkdir -p /usr/app/src /usr/app/virtualenv

RUN chown -R 10000:10000 /usr/app

RUN pip install virtualenv

USER 10000

RUN virtualenv /usr/app/virtualenv

WORKDIR /usr/app/src
ENV PATH /usr/app/virtualenv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV PYTHONPATH /usr/app/src
ENV PYTHONUNBUFFERED 1

COPY requirements.txt requirements.txt
RUN /usr/app/virtualenv/bin/pip install --no-cache -r requirements.txt
