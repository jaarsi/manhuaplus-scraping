FROM python:3.10-slim
ENV TZ="America/Sao_Paulo"
ENV PYTHONUNBUFFERED=1
WORKDIR /tmp/app
COPY . .
RUN pip install .
CMD [ "python", "-m", "series_scraping", "scrape", "start" ]
