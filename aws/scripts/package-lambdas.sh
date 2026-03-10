#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

mkdir -p build

cd upload_function
zip -j ../build/upload-function.zip lambda_function.py
cd ..

cd process_function
zip -j ../build/process-function.zip lambda_function.py
cd ..

echo "Packages ZIP créés dans aws/build/"