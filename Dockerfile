FROM python:3.10-slim
ENV TZ="America/Sao_Paulo"
ENV PYTHONUNBUFFERED=1
RUN mkdir /tmp/app
WORKDIR /tmp/app
COPY . .
RUN pip install .
CMD ["python", "-m", "manhuaplus_scraping"]
