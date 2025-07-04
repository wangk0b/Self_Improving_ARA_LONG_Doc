#!/bin/bash

data_path="/mnt/azureml/cr/j/33f053f07b6742588ce31b1e9323cf15/cap/data-capability/wd/raw_docs_out/temp/redis/data"

redis-server --dir $data_path \
             --dbfilename dump.rdb \
             --daemonize yes \
             --port 6379 \
             --bind 127.0.0.1 \
             --save 60 1
