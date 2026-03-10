import os
import json
import uuid
import logging
from datetime import datetime, timezone

import azure.functions as func
from azure.storage.blob import BlobServiceClient
from azure.data.tables import TableServiceClient

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

AZURITE_CONNECTION_STRING = os.getenv("AZURITE_CONNECTION_STRING")
BLOB_CONTAINER_NAME = os.getenv("BLOB_CONTAINER_NAME", "incoming")
TABLE_NAME = os.getenv("TABLE_NAME", "tpresults")


def get_blob_service_client():
    return BlobServiceClient.from_connection_string(AZURITE_CONNECTION_STRING)


def get_table_service_client():
    return TableServiceClient.from_connection_string(AZURITE_CONNECTION_STRING)


@app.route(route="upload", methods=["POST"])
def upload(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("HTTP upload trigger received a request.")

    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            "Le body doit être un JSON valide.",
            status_code=400
        )

    name = body.get("name")
    content = body.get("content")

    if not name or not content:
        return func.HttpResponse(
            "Le JSON doit contenir 'name' et 'content'.",
            status_code=400
        )

    try:
        blob_service = get_blob_service_client()
        container_client = blob_service.get_container_client(BLOB_CONTAINER_NAME)
        container_client.create_container()
    except Exception:
        pass

    blob_client = blob_service.get_blob_client(
        container=BLOB_CONTAINER_NAME,
        blob=name
    )
    blob_client.upload_blob(content.encode("utf-8"), overwrite=True)

    return func.HttpResponse(
        json.dumps({
            "message": "Blob uploadé avec succès",
            "container": BLOB_CONTAINER_NAME,
            "blob_name": name
        }, ensure_ascii=False),
        status_code=200,
        mimetype="application/json"
    )


@app.blob_trigger(
    arg_name="myblob",
    path="incoming/{name}",
    connection="AzureWebJobsStorage"
)
def process_blob(myblob: func.InputStream):
    blob_name = myblob.name.split("/")[-1]
    blob_bytes = myblob.read()
    text = blob_bytes.decode("utf-8", errors="replace")

    logging.info(f"Blob trigger exécuté pour {blob_name}")

    table_service = get_table_service_client()
    table_client = table_service.create_table_if_not_exists(TABLE_NAME)

    entity = {
        "PartitionKey": "processed",
        "RowKey": str(uuid.uuid4()),
        "fileName": blob_name,
        "processedAt": datetime.now(timezone.utc).isoformat(),
        "size": len(blob_bytes),
        "preview": text[:100]
    }

    table_client.create_entity(entity=entity)

    logging.info(f"Entity écrite dans Table Storage: {entity}")