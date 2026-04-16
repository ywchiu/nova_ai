#!/bin/bash
# 預先下載 Python 套件，供離線安裝用
# 在有網路的電腦跑，產出的 packages/ 資料夾帶去客戶端

mkdir -p packages
pip download -r requirements.txt -d packages/
echo ""
echo "=== 離線安裝方式（在客戶電腦）==="
echo "pip install --no-index --find-links=packages/ -r requirements.txt"
