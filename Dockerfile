FROM python:slim-bullseye
WORKDIR /tools
COPY replacer.py ./
RUN apt update
RUN apt install wget -y
RUN ARCH=$(dpkg --print-architecture) VERSION=$(curl -L -s https://dl.k8s.io/release/stable.txt) wget https://dl.k8s.io/release/$VERSION/bin/linux/$ARCH/kubectl
RUN chmod +x kubectl
RUN ARCH=$(dpkg --print-architecture) && wget https://get.helm.sh/helm-v3.10.3-linux-$ARCH.tar.gz && tar xf helm-v3.10.3-linux-$ARCH.tar.gz && mv linux-$ARCH/helm ./helm && rm -rf linux-$ARCH helm-v3.10.3-linux-$ARCH.tar.gz
RUN chmod +x helm
RUN pip install kubernetes
