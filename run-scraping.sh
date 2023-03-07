#!/bin/bash
rm -f dist/* \
    && poetry build \
    && docker compose up --build -d
