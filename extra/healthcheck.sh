#!/bin/bash

curl -D - http://127.0.0.1:80/ping || exit 1
