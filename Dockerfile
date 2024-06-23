FROM python:slim-bullseye AS builder
ENV HELM_VERSION=3.10.3
ENV KUSTOMIZE_VERSION=5.4.2
WORKDIR /tools
RUN apt update
RUN apt install dpkg wget tar -y
RUN ARCH="$(dpkg --print-architecture)" && wget "https://get.helm.sh/helm-v${HELM_VERSION}-linux-${ARCH}.tar.gz" && tar xf "./helm-v${HELM_VERSION}-linux-${ARCH}.tar.gz"
RUN ARCH="$(dpkg --print-architecture)" && wget "https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2Fv${KUSTOMIZE_VERSION}/kustomize_v${KUSTOMIZE_VERSION}_linux_${ARCH}.tar.gz" && tar xf "./kustomize_v${KUSTOMIZE_VERSION}_linux_${ARCH}.tar.gz"

FROM python:3.10.14-alpine3.20 AS runner
WORKDIR /tools
COPY ./requirements.txt ./
COPY ./*.py ./
COPY --from=builder /tools/linux-*/helm ./
COPY --from=builder /tools/kustomize ./
RUN apk --no-cache add bash
RUN chmod +x ./helm ./kustomize
RUN pip install --no-cache-dir -r ./requirements.txt
RUN rm -f ./requirements.txt