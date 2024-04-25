import json
import os

import utils


PROCESS_MEDIA = {
    'title': 'Media processing',
    'run': [
        {'cmd': 'resize_img', 'machine': 'basic', 'no_output': True, 'wait_for': 10},
    ],
}


if __name__ == '__main__':
    s3 = utils.s3_client(local=True)
    filename = 'example_img.jpg'
    example_file = open(filename, 'wb').close()
    with open(filename, 'rb') as media_f:
        s3.put_object(
            Body=media_f,
            Bucket=os.environ.get('LD_S3_BUCKET'),
            Key=f'in/img/{filename}',
            Metadata={'ld_code': json.dumps(PROCESS_MEDIA)},
        )