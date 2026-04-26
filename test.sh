#!/bin/bash

operation="${1:-off}"

case "${operation}" in
    on|off)
        ;;
    *)
        echo "usage: $0 [on|off]" >&2
        exit 1
        ;;
esac

curl -D - \
    http://127.0.0.1:8000/deepping

curl -D - \
    -X POST \
    -H "Content-Type: application/json" \
    -d "{\"operation\": \"${operation}\"}" \
    http://127.0.0.1:8000/plug/key123
