import json
import os
import urllib.parse
import boto3

sns = boto3.client("sns")

TOPIC_ARN = os.environ["TOPIC_ARN"]
UPLOAD_BUCKET = os.environ["UPLOAD_BUCKET"]

def lambda_handler(event, context):
    # S3 event -> publish a message into SNS
    records = event.get("Records", [])
    published = 0

    for r in records:
        s3 = r.get("s3", {})
        bucket = s3.get("bucket", {}).get("name")
        key = urllib.parse.unquote_plus(s3.get("object", {}).get("key", ""))

        if not bucket or not key:
            continue

        message = {
            "bucket": bucket,
            "key": key,
            "source": "s3_event",
        }

        sns.publish(
            TopicArn=TOPIC_ARN,
            Message=json.dumps(message),
            MessageAttributes={
                "eventType": {"DataType": "String", "StringValue": "ImageUploaded"}
            }
        )
        published += 1

    return {"ok": True, "published": published, "uploadBucketExpected": UPLOAD_BUCKET}
