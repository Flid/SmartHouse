FROM arm32v7/python:3.6-slim
MAINTAINER "Anton Kirilenko" <antony.kirilenko@gmail.com>


ENV QEMU_EXECVE 1
ENV ROOT /opt/smart_house/deployer/
ENV RUN_USER deployer-user

COPY qemu/cross-build-end qemu/cross-build-start qemu/qemu-arm-static qemu/sh-shim /usr/bin/
RUN if [ $(uname -p) = "x86_64" ] ; then cross-build-start; fi
#RUN ["/bin/bash", "-c", "if [[ $(uname -p) == 'x86_64' ]]; then cross-build-start; fi"]
#RUN [ "cross-build-start" ]

# Create the user that will run the app
RUN groupadd -r $RUN_USER && useradd -r -g $RUN_USER $RUN_USER

#RUN apt-get update && apt-get install -y git software-properties-common

# Requirements first, to allow for better Docker layer caching
COPY requirements.txt $ROOT/requirements.txt
RUN pip install -r $ROOT/requirements.txt

COPY . $ROOT
WORKDIR $ROOT

EXPOSE 8899

#RUN ["/bin/bash", "-c", "if [[ $(uname -p) == 'x86_64' ]]; then cross-build-end; fi"]
RUN if [ $(uname -p) == 'x86_64' ] ; then cross-build-end; fi

USER $RUN_USER

CMD ["./run.sh"]
