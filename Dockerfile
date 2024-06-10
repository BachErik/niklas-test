FROM python:3.12.4-bullseye
WORKDIR /tools
COPY test-replace.py ./
RUN pip install kubernetes
