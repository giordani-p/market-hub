#!/usr/bin/env bash
set -euo pipefail

QUEUE_NAME="${JOBS_QUEUE_NAME:-market-hub-jobs}"
DLQ_NAME="${JOBS_DLQ_NAME:-market-hub-jobs-dlq}"
MAX_RECEIVE="${JOBS_MAX_RECEIVE_COUNT:-3}"
VISIBILITY="${JOBS_VISIBILITY_TIMEOUT_SECONDS:-60}"
INTERVAL="${JOBS_RECONCILE_INTERVAL_SECONDS:-60}"
RULE_NAME="market-hub-reconcile-priorities"

# A Rule do EventBridge exige a sintaxe rate(n minute[s]); o relogio do
# usuario e so o numero em segundos. No LocalStack a Rule e mock.
if [ "$INTERVAL" -le 0 ]; then
  MINUTES=1
else
  MINUTES=$(( (INTERVAL + 59) / 60 ))
fi
if [ "$MINUTES" -eq 1 ]; then
  SCHEDULE="rate(1 minute)"
else
  SCHEDULE="rate(${MINUTES} minutes)"
fi

awslocal sqs create-queue --queue-name "$DLQ_NAME"
DLQ_URL=$(awslocal sqs get-queue-url --queue-name "$DLQ_NAME" --query QueueUrl --output text)
DLQ_ARN=$(awslocal sqs get-queue-attributes --queue-url "$DLQ_URL" --attribute-names QueueArn --query Attributes.QueueArn --output text)

awslocal sqs create-queue --queue-name "$QUEUE_NAME"
QUEUE_URL=$(awslocal sqs get-queue-url --queue-name "$QUEUE_NAME" --query QueueUrl --output text)
QUEUE_ARN=$(awslocal sqs get-queue-attributes --queue-url "$QUEUE_URL" --attribute-names QueueArn --query Attributes.QueueArn --output text)

python3 - "$QUEUE_URL" "$QUEUE_ARN" "$DLQ_ARN" "$VISIBILITY" "$MAX_RECEIVE" "$RULE_NAME" "$SCHEDULE" <<'PY'
import json
import subprocess
import sys

queue_url, queue_arn, dlq_arn, visibility, max_receive, rule_name, schedule = sys.argv[1:]
redrive = json.dumps({"deadLetterTargetArn": dlq_arn, "maxReceiveCount": str(max_receive)})
policy = json.dumps(
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Service": "events.amazonaws.com"},
                "Action": "sqs:SendMessage",
                "Resource": queue_arn,
            }
        ],
    }
)
attrs = {
    "VisibilityTimeout": str(visibility),
    "RedrivePolicy": redrive,
    "Policy": policy,
}
subprocess.check_call(
    ["awslocal", "sqs", "set-queue-attributes", "--queue-url", queue_url, "--attributes", json.dumps(attrs)]
)
subprocess.check_call(
    ["awslocal", "events", "put-rule", "--name", rule_name, "--schedule-expression", schedule, "--state", "ENABLED"]
)
targets = json.dumps(
    [{"Id": "jobs", "Arn": queue_arn, "Input": json.dumps({"job_type": "RECONCILE_PRIORITIES"})}]
)
subprocess.check_call(
    ["awslocal", "events", "put-targets", "--rule", rule_name, "--targets", targets]
)
PY
