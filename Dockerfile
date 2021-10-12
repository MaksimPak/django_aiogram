FROM python:3
ENV PYTHONUNBUFFERED 1
RUN mkdir /parcel
COPY ./entrypoint.sh /
RUN chmod 777 /entrypoint.sh

WORKDIR /parcel
COPY /src/requirements.txt /parcel/

RUN pip install -r requirements.txt && apt update && \
    apt install -y ffmpeg netcat && \
    apt install -y gdal-bin

COPY . /parcel/
ENTRYPOINT ["/entrypoint.sh"]