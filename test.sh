#!/bin/bash

curl -D - \
    -X POST \
    -H "Content-Type: application/json" \
    -d '{"operation": "on"}' \
    http://127.0.0.1:8000/plug/key123
