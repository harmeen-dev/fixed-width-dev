FROM ubuntu:18.10
RUN apt-get update && apt-get install -y --no-install-recommends apt-utils
RUN apt-get install apt-transport-https -y
RUN apt-get install software-properties-common -y
#RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update
RUN apt-get install python3.7 -y
RUN apt-get install python3.7-dev -y
RUN apt-get install -y python3-pip

ENV FIXED_WIDTH $FIXED_WIDTH

COPY spec.json /opt/app/spec.json
COPY requirements.txt /opt/app/requirements.txt
WORKDIR /opt/app
RUN python3.7 -m pip install -r requirements.txt
COPY . /opt/app

CMD python3.7 fixed_width_csv.py $FIXED_WIDTH
#CMD [ "python3.7", "fixed_width_csv.py", $FIXED_WIDTH]
