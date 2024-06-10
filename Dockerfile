FROM python:slim-bullseye
WORKDIR /tools
COPY test-replace.py ./
RUN pip install kubernetes
