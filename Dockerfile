FROM arm32v7/python:3.6-slim
MAINTAINER "Anton Kirilenko" <antony.kirilenko@gmail.com>

ENV QEMU_EXECVE 1
ENV ROOT /opt/snailshell/control_panel/
ENV STATIC_ROOT $ROOT/static
ENV RUN_USER snailshell-cp-user

COPY qemu/cross-build-end qemu/cross-build-start qemu/qemu-arm-static qemu/sh-shim /usr/bin/
RUN ["cross-build-start"]

# Create the user that will run the app
RUN groupadd -r $RUN_USER && useradd -r -g $RUN_USER $RUN_USER
RUN mkdir -p $STATIC_ROOT && chown $RUN_USER:$RUN_USER $STATIC_ROOT -R

RUN apt-get update && apt-get install -y gcc libffi-dev openssl-dev build-base

# Requirements first, to allow for better Docker layer caching
COPY requirements.txt $ROOT/requirements.txt
RUN pip install -r $ROOT/requirements.txt

COPY . $ROOT
WORKDIR $ROOT

EXPOSE 8000

RUN ["cross-build-end"]

USER $RUN_USER

CMD ["./run.sh"]
