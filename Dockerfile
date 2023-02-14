FROM python:3.10-slim
ENV PYTHONUNBUFFERED=1
RUN mkdir /app
WORKDIR /app
RUN pip install playwright \
    && playwright install-deps firefox \
    && playwright install firefox
COPY manhuaplus-series.toml dist/manhuaplus_scraping*.tar.gz .
RUN pip install manhuaplus_scraping*.tar.gz
CMD ["python", "-m", "manhuaplus_scraping"]
