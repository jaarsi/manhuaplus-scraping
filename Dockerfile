FROM python:3.10-slim
ENV PYTHONUNBUFFERED=1
RUN mkdir /app
WORKDIR /app
COPY dist/manhuaplus_scraping*.tar.gz .
RUN pip install manhuaplus_scraping*.tar.gz \
    && playwright install-deps firefox \
    && playwright install firefox
CMD ["python", "-u", "-m", "manhuaplus_scraping"]
