import json
import os
import boto3

S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://localhost:4566")
BUCKET_NAME = os.getenv("BUCKET_NAME", "mon-bucket-tp")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-1")

s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=AWS_REGION,
    aws_access_key_id="test",
    aws_secret_access_key="test"
)

def lambda_handler(event, context):
    name = event.get("name")
    content = event.get("content")

    if not name or not content:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Le payload doit contenir 'name' et 'content'"})
        }

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=name,
        Body=content.encode("utf-8")
    )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Objet S3 créé",
            "bucket": BUCKET_NAME,
            "key": name
        })
    }