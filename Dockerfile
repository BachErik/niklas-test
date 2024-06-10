FROM python:slim-bullseye
WORKDIR /tools
COPY test-replace.py ./
RUN apt update
RUN apt install wget -y
RUN ARCH=$(dpkg --print-architecture) && wget https://get.helm.sh/helm-v3.10.3-linux-$ARCH.tar.gz && tar xf helm-v3.10.3-linux-$ARCH.tar.gz && mv linux-$ARCH/helm ./helm
RUN chmod +x helm
RUN pip install kubernetes
