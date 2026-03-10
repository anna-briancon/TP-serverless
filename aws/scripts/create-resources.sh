#!/usr/bin/env bash
set -e

ENDPOINT="http://localhost:4566"
REGION="eu-west-1"
ACCOUNT_ID="000000000000"
ROLE_ARN="arn:aws:iam::$ACCOUNT_ID:role/lambda-role"

aws --endpoint-url=$ENDPOINT iam create-role \
  --role-name lambda-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": { "Service": "lambda.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }]
  }' || true

aws --endpoint-url=$ENDPOINT s3 mb s3://mon-bucket-tp || true

aws --endpoint-url=$ENDPOINT dynamodb create-table \
  --table-name tp-results \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST || true

aws --endpoint-url=$ENDPOINT lambda create-function \
  --function-name upload-function \
  --runtime python3.12 \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://aws/build/upload-function.zip \
  --role $ROLE_ARN \
  --environment 'Variables={S3_ENDPOINT=http://host.docker.internal:4566,BUCKET_NAME=mon-bucket-tp,AWS_REGION=eu-west-1}'

aws --endpoint-url=$ENDPOINT lambda create-function \
  --function-name process-function \
  --runtime python3.12 \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://aws/build/process-function.zip \
  --role $ROLE_ARN \
  --environment 'Variables={AWS_ENDPOINT=http://host.docker.internal:4566,TABLE_NAME=tp-results,AWS_REGION=eu-west-1}'

aws --endpoint-url=$ENDPOINT lambda add-permission \
  --function-name process-function \
  --statement-id s3invoke \
  --action lambda:InvokeFunction \
  --principal s3.amazonaws.com \
  --source-arn arn:aws:s3:::mon-bucket-tp || true

aws --endpoint-url=$ENDPOINT s3api put-bucket-notification-configuration \
  --bucket mon-bucket-tp \
  --notification-configuration '{
    "LambdaFunctionConfigurations": [{
      "LambdaFunctionArn": "arn:aws:lambda:eu-west-1:000000000000:function:process-function",
      "Events": ["s3:ObjectCreated:*"]
    }]
  }'

echo "Ressources LocalStack créées."