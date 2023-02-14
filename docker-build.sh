#!/bin/bash
rm dist/* && poetry build && docker compose build
