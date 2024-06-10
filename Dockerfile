FROM python:slim-bullseye
WORKDIR /tools
COPY test-replace.py ./
RUN pip install kubernetes
RUN ARCH=$(dpkg --print-architecture) && wget https://get.helm.sh/helm-v3.10.3-linux-$ARCH.tar.gz && tar xf helm-v3.10.3-linux-$ARCH.tar.gz && mv linux-$ARCH/helm ./helm
RUN chmod +x helm
