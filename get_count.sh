#!/bin/bash

FILE=./data/upcoming.json

jq '[.bins[].elements | length] | add' "$FILE"
