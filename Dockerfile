FROM python:3
ENV PYTHONUNBUFFERED 1
RUN mkdir /parcel
WORKDIR /parcel
COPY /src/requirements.txt /parcel/

RUN pip install -r  requirements.txt
RUN apt update
RUN apt install -y ffmpeg
COPY . /parcel/