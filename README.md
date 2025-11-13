# Kasa Webhook

Turn kasa smart plugs on/off via a webhook. It's a replacement of ifttt webhook
which requires pro plan now.

## Usage

### Docker Compose

```bash
docker-compose up -d
```

### Docker CLI

```bash
docker run -d \
  -e KASA_WEBHOOK_PLUGS='[{"name":"phone-charger","host":"192.168.89.64"}]' \
  -e KASA_WEBHOOK_KEYS='{"<some-keys>": "phone-charger"}' \
  ghcr.io/genzj/kasa-webhook:latest
```

## Development

### Setup with mise and poetry

```bash
mise install
poetry install
```

### Configure environment

```bash
cp .env.sample .env
# Edit .env with your plug configurations
```

### Start locally with uvicorn

```bash
uvicorn kasa_webhook.api:app --log-config logging_conf.yaml --port 8080 --reload
```
