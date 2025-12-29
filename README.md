# Event-Driven Image Processing Pipeline

A fully serverless, event-driven architecture built on AWS that processes image uploads asynchronously using S3, Lambda, SNS, and SQS.

This project demonstrates decoupled design, fan-out messaging, fault tolerance, and production-grade infrastructure deployment using AWS SAM and CloudFormation.

## Architecture Overview

This system processes image uploads through a multi-stage asynchronous pipeline:

```
S3 (Upload Bucket)
       │
       ▼ ObjectCreated (.jpg)
Lambda (Ingest Function)
       │
       ▼ Publish
   SNS Topic (Fan-out)
       │
       ▼ Subscription
   SQS Queue (+ DLQ)
       │
       ▼ Event Source Mapping
Lambda (Worker Function)
       │
       ▼ Output
S3 (Processed Bucket)
```

### Why This Architecture?

- **Loose coupling** between producers and consumers
- **Scalable fan-out** via SNS
- **Back-pressure handling** with SQS
- **Failure isolation** using a Dead-Letter Queue (DLQ)
- **Fully serverless** — no EC2, no containers, no servers to manage

## Key Design Decisions

| Design Choice | Rationale |
|---------------|-----------|
| S3 → Lambda trigger | Event-driven ingestion without polling |
| SNS fan-out | Enables future consumers without redesign |
| SQS buffering | Protects downstream workers from traffic spikes |
| Dead-Letter Queue | Prevents poison-pill messages from blocking the pipeline |
| Separate stacks | Avoids circular dependencies in CloudFormation |
| Custom Resource for S3 notifications | Works around CloudFormation limitation |
| Infrastructure as Code | Repeatable, auditable, version-controlled deployments |

## Infrastructure Components

### Core Stack (`image-pipeline-core`)

Provisioned using AWS SAM:

- S3 Upload Bucket (server-side encryption enabled)
- S3 Processed Bucket (server-side encryption enabled)
- Ingest Lambda (Python 3.12)
- SNS Topic
- SQS Queue + Dead-Letter Queue
- Worker Lambda
- IAM roles with least-privilege permissions
- Event source mapping (SQS → Lambda)

### Notification Stack (`image-pipeline-notifications`)

Provisioned using a CloudFormation Custom Resource:

- Lambda-backed custom resource
- Attaches S3 → Lambda notification after core resources exist
- Breaks CloudFormation circular dependency safely

## Repository Structure

```
aws-image-pipeline-s3-sns-sqs-lambda/
├── infrastructure/
│   ├── template.yaml              # Core SAM stack
│   └── notifications.yaml         # Custom resource for S3 notifications
├── src/
│   ├── ingest/
│   │   └── app.py                 # Ingest Lambda function
│   └── worker/
│       └── app.py                 # Worker Lambda function
├── diagrams/
│   └── architecture.png           # Architecture diagram
└── README.md
```

## Deployment

> All development and deployment performed via WSL terminal (CLI-only)

### Prerequisites

- AWS CLI configured with appropriate credentials
- AWS SAM CLI installed
- Python 3.12

### Step 1: Deploy Core Infrastructure

```bash
sam build -t infrastructure/template.yaml
sam deploy --guided
```

Stack outputs include:
- Upload bucket name
- Ingest Lambda ARN

### Step 2: Export Stack Outputs

```bash
UPLOAD_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name image-pipeline-core \
  --query "Stacks[0].Outputs[?OutputKey=='UploadBucket'].OutputValue" \
  --output text)

INGEST_ARN=$(aws cloudformation describe-stacks \
  --stack-name image-pipeline-core \
  --query "Stacks[0].Outputs[?OutputKey=='IngestFunctionArn'].OutputValue" \
  --output text)
```

### Step 3: Attach S3 Notifications

This separate deployment avoids circular dependency issues:

```bash
aws cloudformation deploy \
  --stack-name image-pipeline-notifications \
  --template-file infrastructure/notifications.yaml \
  --parameter-overrides \
    BucketName=$UPLOAD_BUCKET \
    LambdaArn=$INGEST_ARN \
  --capabilities CAPABILITY_NAMED_IAM
```

## Testing the Pipeline

Upload a test image:

```bash
aws s3 cp test.jpg s3://$UPLOAD_BUCKET/test.jpg
```

Verify the pipeline by checking:

1. CloudWatch logs for `IngestFunction`
2. CloudWatch logs for `WorkerFunction`
3. Output object written to processed bucket
4. No messages stuck in the DLQ

## Security Best Practices

- Least-privilege IAM policies
- Server-side encryption on all S3 buckets
- Dead-Letter Queue for failure isolation
- No hard-coded credentials
- Event-driven design with no open inbound access

## Scalability and Fault Tolerance

- **Horizontal scaling** handled automatically by Lambda concurrency
- **SQS buffering** absorbs traffic spikes
- **DLQ** protects against repeated failures from poison-pill messages
- **Independent services** can be swapped or extended without affecting the pipeline

## Future Enhancements

- [ ] Image resizing and metadata extraction
- [ ] Amazon Rekognition integration for image analysis
- [ ] CloudWatch alarms on DLQ depth
- [ ] Multiple SNS subscribers for parallel processing
- [ ] Step Functions orchestration for complex workflows
- [ ] CI/CD pipeline via GitHub Actions

## Skills Demonstrated

- AWS Solutions Architect Associate (SAA-C03) design patterns
- Event-driven architectures
- Asynchronous messaging with SNS/SQS
- AWS SAM and CloudFormation
- Debugging complex CloudFormation rollback states
- Production-grade serverless design

## Author

**Joseph McCoy**

AWS | DevOps | Serverless | Python

[![GitHub](https://img.shields.io/badge/GitHub-jmac052002-181717?style=flat&logo=github)](https://github.com/jmac052002)
