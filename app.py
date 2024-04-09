import json
import os

import boto3


def run_workflow(s3_client):
    """Run a 2-step line_d workflow"""
    workflow = {
        'title': 'Example workflow',
        'run': [
            {'cmd': 'task_a', 'machine': 'basic', 'no_output': True, 'wait_for': 10},
            {'cmd': 'task_b', 'machine': 'basic', 'no_output': True, 'wait_for': 10},
        ],
    }
    return s3_client.put_object(
        Body=json.dumps(workflow).encode('utf-8'),
        Bucket=os.environ.get('LD_S3_BUCKET'),
        Key='in/example',
        Metadata={'ld_manage': 'true'},
    )


if __name__ == '__main__':
    # setup_local_env()
    aws = boto3.session.Session(
        aws_access_key_id=os.environ.get('LD_AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('LD_AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.environ.get('LD_AWS_SESSION_TOKEN'),
        region_name='us-east-1',
    )
    s3_client = aws.client('s3')
    run_workflow(s3_client)