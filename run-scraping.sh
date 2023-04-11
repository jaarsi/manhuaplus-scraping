#!/bin/bash
rm -f dist/* \
    && poetry build \
    && docker compose up --remove-orphans --build -d
