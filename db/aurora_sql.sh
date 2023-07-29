#!/bin/bash

# Set your AWS region and Aurora cluster identifier
AWS_REGION="us-east-2c"
AURORA_CLUSTER_IDENTIFIER="botty-db-cluster-1"

# Get the SQL file name from CLI argument
if [ -z "$1" ]; then
  echo "Usage: $0 <sql_file_name>"
  exit 1
fi

# The name of the SQL file to execute
SQL_FILE="$1"

# Check if the SQL file exists
if [ ! -f "$SQL_FILE" ]; then
  echo "Error: SQL file '$SQL_FILE' not found."
  exit 1
fi

# Read SQL statements from the chosen file
sql_content=$(cat "$SQL_FILE")

# Execute the SQL statements using AWS Data API
echo "Executing SQL from '$SQL_FILE'..."
query_execution_id=$(aws rds-data execute-statement \
  --region us-east-2 \
  --resource-arn arn:aws:rds:us-east-2:913526741104:cluster:botty-dev-cluster \
  --secret-arn arn:aws:secretsmanager:us-east-2:913526741104:secret:botty-db-dev-secret-pX9iZB \
  --database botty-db-dev \
  --sql "$sql_content" \
  --include-result-metadata)

# Wait for the query execution to complete (optional)
aws rds-data wait sql \
  --region us-east-2 \
  --resource-arn arn:aws:rds:us-east-2:913526741104:cluster:botty-db-cluster-1 \
  --query-id $query_execution_id

