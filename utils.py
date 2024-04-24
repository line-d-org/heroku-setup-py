import json
import os
import subprocess

import boto3


def setup_local_env():
    """Add Heroku Config variables to local environment"""
    heroku_config_out = subprocess.check_output('heroku config -j', shell=True)
    heroku_env = json.loads(heroku_config_out)
    for k, v in heroku_env.items():
        os.environ[k] = v


def s3_client(local=False):
    if local:
        setup_local_env()

    aws = boto3.session.Session(
        aws_access_key_id=os.environ.get('LD_AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('LD_AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.environ.get('LD_AWS_SESSION_TOKEN'),
        region_name=os.environ.get('LD_REGION', 'us-east-1'),
    )
    return aws.client('s3')