import json
import os
import boto3
from datetime import datetime, timezone

s3 = boto3.client("s3")
PROCESSED_BUCKET = os.environ["PROCESSED_BUCKET"]

def lambda_handler(event, context):
    # SQS event -> each record contains the SNS "raw message" body (we set RawMessageDelivery=true)
    processed = 0

    for record in event.get("Records", []):
        body = record.get("body", "{}")
        msg = json.loads(body)

        bucket = msg.get("bucket")
        key = msg.get("key")

        # Demo "processing": write a result JSON into processed bucket
        out_key = f"results/{key}.json".replace("//", "/")
        payload = {
            "bucket": bucket,
            "key": key,
            "processedAt": datetime.now(timezone.utc).isoformat(),
            "status": "OK",
        }

        s3.put_object(
            Bucket=PROCESSED_BUCKET,
            Key=out_key,
            Body=json.dumps(payload, indent=2).encode("utf-8"),
            ContentType="application/json",
        )
        processed += 1

    return {"ok": True, "processed": processed, "processedBucket": PROCESSED_BUCKET}
