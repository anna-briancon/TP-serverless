import json
import os
import uuid
from datetime import datetime, timezone
from urllib.parse import unquote_plus

import boto3

AWS_ENDPOINT = os.getenv("AWS_ENDPOINT", "http://localhost:4566")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-1")
TABLE_NAME = os.getenv("TABLE_NAME", "tp-results")

s3 = boto3.client(
    "s3",
    endpoint_url=AWS_ENDPOINT,
    region_name=AWS_REGION,
    aws_access_key_id="test",
    aws_secret_access_key="test"
)

dynamodb = boto3.resource(
    "dynamodb",
    endpoint_url=AWS_ENDPOINT,
    region_name=AWS_REGION,
    aws_access_key_id="test",
    aws_secret_access_key="test"
)

def lambda_handler(event, context):
    table = dynamodb.Table(TABLE_NAME)

    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = unquote_plus(record["s3"]["object"]["key"])

        obj = s3.get_object(Bucket=bucket, Key=key)
        content_bytes = obj["Body"].read()
        content_text = content_bytes.decode("utf-8", errors="replace")

        item = {
            "id": str(uuid.uuid4()),
            "fileName": key,
            "processedAt": datetime.now(timezone.utc).isoformat(),
            "size": len(content_bytes),
            "preview": content_text[:100]
        }

        table.put_item(Item=item)

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Traitement terminé"})
    }