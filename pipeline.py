import json
import os 

import utils


def gen_tasks(cmd:str, endpoints:list, dyno_size:str ='basic', no_output=False):
    tasks = []
    for endpoint in endpoints:
        options = [
            f'endpoint={endpoint}', 
            f'output_file=etl/{endpoint}.json'
        ]
        task = {
            'cmd': cmd,
            'machine': dyno_size,
            'options': options,
            'no_output': no_output,
        }
        tasks.append(task)
    return tasks



ENDPOINTS = ['posts', 'users', 'comments', 'albums']
ELT_PIPELINE = {
    'title': 'Get JSON in parallel',
    'run': [
        {
            'name': 'Fetch JSON (parallel)',
            'parallel': gen_tasks(cmd='get_json', endpoints=ENDPOINTS)
        },
        {
            'name': 'Load JSON (parallel)',
            'parallel': gen_tasks(cmd='load_json', endpoints=ENDPOINTS)
        },
        {
            'name': 'Run transforms with DBT',
            'cmd': 'dbt',
            'machine': 'basic',
            'no_output': True,
            'timeout': 120,
        },
    ],
}


if __name__ == '__main__':
    s3 = utils.s3_client()
    s3.put_object(
        Body=json.dumps(ELT_PIPELINE),
        Bucket=os.environ.get('LD_S3_BUCKET'),
        Key='in/elt_pipeline.json',
        Metadata={'ld_manage': 'true'},
    )