FROM python:3.10-slim
ENV TZ="America/Sao_Paulo"
ENV PYTHONUNBUFFERED=1
RUN mkdir /app
WORKDIR /app
RUN pip install playwright \
    && playwright install-deps firefox \
    && playwright install firefox
COPY settings.toml dist/manhuaplus_scraping*.tar.gz .
RUN pip install manhuaplus_scraping*.tar.gz
CMD ["python", "-m", "manhuaplus_scraping"]
