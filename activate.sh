#!/bin/bash

# 获取当前脚本所在的目录
DIR=$(dirname $(realpath "$0"))

# 将目录添加到 PYTHONPATH
export PYTHONPATH="$PYTHONPATH:$DIR"

# 输出确认信息
echo "Current directory '$DIR' has been added to PYTHONPATH"
