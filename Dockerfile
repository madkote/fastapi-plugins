FROM python:3.8-alpine as demo
LABEL maintainer="madkote(at)bluewin.ch"
RUN apk --update add --no-cache --virtual MY_DEV_PACK alpine-sdk build-base python3-dev
RUN pip3 install fastapi-plugins[all] uvicorn
RUN mkdir -p /usr/src/app
COPY ./scripts/demo_app.py /usr/src/app
WORKDIR /usr/src/app
EXPOSE 8000
CMD ["uvicorn", "--host", "0.0.0.0", "demo_app:app"]
