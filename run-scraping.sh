#!/bin/bash
rm dist/* && poetry build && docker compose up --build
