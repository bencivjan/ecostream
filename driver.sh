#!/bin/bash

trap "exit" INT TERM
trap "kill 0" EXIT

python3 server.py --profiling_interval 1 &
SERVER_PID=$!

python3 client.py
CLIENT_PID=$!