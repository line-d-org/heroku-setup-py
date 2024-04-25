import os
import json
import time

import requests

import utils


S3 = utils.s3_client()


def get_json():
    ld_env = json.loads(os.environ['line_D'])
    endpoint = ld_env['options'].get('endpoint', 'posts')
    output_file = ld_env['options'].get('output_file', f'etl/{endpoint}.json')
    task_id = ld_env['task_id']
    url = f'https://jsonplaceholder.typicode.com/{endpoint}'

    resp = requests.get(url)
    num_records = 0
    records = []
    if resp.status_code == 200:
        records = resp.json()
        num_records = len(records)

    # Store state for monitoring and composing workflow stages
    state = {
        'endpoint': endpoint,
        'resp_status_code': resp.status_code,
        'num_records': num_records,
        'resp_time': str(resp.elapsed),
    }
    S3.put_object(
        Body=json.dumps(records).encode('utf-8'),
        Bucket=os.environ.get('LD_S3_BUCKET'),
        Key=output_file,
        Metadata={
            'ld_task_id': task_id,
            'ld_state': json.dumps(state),
        },
    )


def load_json():
    ld_env = json.loads(os.environ['line_D'])
    endpoint = ld_env['options'].get('endpoint', 'posts')
    output_file = ld_env['options'].get('output_file', f'etl/{endpoint}.json')
    task_id = ld_env['task_id']

    s3_file = S3.get_object(
        Bucket=os.environ.get('LD_S3_BUCKET'),
        Key=output_file,
    )
    try:
        records = json.loads(s3_file['Body'].read().decode('utf-8'))
    except ValueError:
        records = []

    print('Loading records to Database...')
    time.sleep(3)
    load_output_logs = 'Records loaded successfully. Additional info..'
    state = {
        'endpoint': endpoint,
        'output_file': output_file,
        'num_records': len(records),
    }
    S3.put_object(
        Body=load_output_logs,
        Bucket=os.environ.get('LD_S3_BUCKET'),
        Key=output_file,
        Metadata={
            'ld_task_id': task_id,
            'ld_state': json.dumps(state),
        },
    )


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        fn_name = sys.argv[1]
        fn = locals().get(fn_name, None)
        if fn is not None:
            fn()
