import json
import os

import utils


QUICKSTART = {
    'title': 'Quickstart workflow',
    'run': [
        {'cmd': 'task_a', 'machine': 'basic', 'no_output': True, 'wait_for': 10},
        {'cmd': 'task_b', 'machine': 'basic', 'no_output': True, 'wait_for': 10},
    ],
}


if __name__ == '__main__':
    s3 = utils.s3_client(local=True)
    s3.put_object(
        Body=json.dumps(QUICKSTART).encode('utf-8'),
        Bucket=os.environ.get('LD_S3_BUCKET'),
        Key='in/quickstart_workflow.json',
        Metadata={'ld_manage': 'true'},
    )