FROM python:3.7-alpine as demo
LABEL maintainer="madkote(at)bluewin.ch"
RUN pip3 install fastapi-plugins uvicorn
RUN mkdir -p /usr/src/app
COPY ./scripts/demo.py /usr/src/app
WORKDIR /usr/src/app
EXPOSE 8000
CMD ["uvicorn", "demo_app:app"]
