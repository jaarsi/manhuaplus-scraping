### Requirements
- Docker

### Setup
1. Clone the repository
2. On **docker-compose.yml** file:
    - Set **DISCORD_WH** environment variable to match your notification channel. If you doesn`t have one, google it (discord channel webhook) to create. Super Ez.
3. Fill **manhuaplus-series.toml** with data.

### Running on docker
1. Hit ``./run-scraping.sh`` on terminal.
2. Run ``docker compose logs app`` to see logs.

### Stopping the scraping
1. Run ``docker compose down``.
