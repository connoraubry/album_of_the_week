#!/bin/bash

BASE_DIR="./backups"
OUT_FOLDER="${BASE_DIR}/$(date -I)"

echo $OUT_FOLDER

scp -r server:~/album_of_the_week/data/ "$OUT_FOLDER"
