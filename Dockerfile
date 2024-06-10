FROM python:alpine3.20
WORKDIR /tools
COPY test-replace.py ./
RUN pip install kubernetes
