import boto3
from botocore.exceptions import ClientError

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env
for ep in [Path(__file__).parent / '.env', Path(__file__).parent.parent / '.env', Path(__file__).parent.parent.parent / '.env']:
    if ep.exists():
        load_dotenv(dotenv_path=ep, override=True)

credentials = [
    {
        "name": "S3 Bucket 1",
        "key": os.getenv("AWS_ACCESS_KEY"),
        "secret": os.getenv("AWS_SECRET_KEY"),
        "region": os.getenv("AWS_REGION", "us-east-1"),
        "bucket": os.getenv("S3_BUCKET_NAME", "default-bucket-name")
    }
]

for cred in credentials:
    print(f"\nTesting {cred['name']}...")
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=cred['key'],
            aws_secret_access_key=cred['secret'],
            region_name=cred['region']
        )
        s3.list_buckets()
        print(f"  [OK] Valid credentials for {cred['name']}")
        
        try:
            s3.head_bucket(Bucket=cred['bucket'])
            print(f"  [OK] Bucket access successful for {cred['bucket']}")
        except ClientError as e:
            print(f"  [X] Bucket access failed: {e}")
            
    except ClientError as e:
        print(f"  [X] Credentials invalid: {e}")
    except Exception as e:
        print(f"  [X] Error: {e}")
