FROM python:3.6-slim
MAINTAINER "Anton Kirilenko" <antony.kirilenko@gmail.com>

ENV ROOT /opt/smart_house/testapp/
ENV RUN_USER testapp-user

# Create the user that will run the app
RUN groupadd -r $RUN_USER && useradd -r -g $RUN_USER $RUN_USER

RUN apt-get update && apt-get install -y git python-software-properties software-properties-common gcc libpq-dev python3-dev
RUN apt-get install qemu-user-static

# Requirements first, to allow for better Docker layer caching
COPY requirements.txt $ROOT/requirements.txt
RUN pip install -r $ROOT/requirements.txt

COPY . $ROOT
WORKDIR $ROOT

EXPOSE 8899

USER $RUN_USER

CMD ["./run.sh"]
