#!/usr/bin/env bash
set -e

ENDPOINT="http://localhost:4566"

aws --endpoint-url=$ENDPOINT lambda invoke \
  --function-name upload-function \
  --payload fileb://aws/payload.json \
  aws/output.json

echo "---- Réponse upload-function ----"
cat aws/output.json
echo

echo "---- Contenu bucket S3 ----"
aws --endpoint-url=$ENDPOINT s3 ls s3://mon-bucket-tp/

echo "---- Scan DynamoDB ----"
aws --endpoint-url=$ENDPOINT dynamodb scan --table-name tp-results