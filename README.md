[line^d](https://elements.heroku.com/addons/line-d) provides advanced Amazon S3 cloud storage with a built-in compute engine. It enhances S3 to include programmable, event-driven workflows. Anytime you add or update files on AWS S3, you can run [dynos](dyno-types).

line^d helps you build "reactive" data lakes where data storage and processing are integrated seamlessly. The compute engine is controlled using JSON instructions within or attached to your S3 files - no other dependencies are required. With many other features like parallelism, retries, and execution guarantees, you can create reliable data workflows without the complexity of a dedicated job queue or compute cluster.

Here are some workflows you can automate with line^d:

* **Data pipelines and ELT**: Define multi-step and parallel workflows for large-scale data pipelines.
* **Image, video, and document processing**: Automate file processing in the background by attaching line^d metadata to your S3 uploads.
* **Log management and monitoring**: Filter, rotate, and summarize your system's log files to create easy, low-cost monitoring workflows.

## Provisioning the Add-on

Attach line^d to a Heroku application via the CLI:

> callout
> Reference the [line^d Elements Page](https://elements.heroku.com/addons/line-d) for a list of available plans and regions.

```term
$ heroku addons:create line-d
Creating line-d-clear-41822 on example-app... free
line-D is being provisioned and will be available shortly.
line-d-clear-41822 is being created in the background. The app will restart when complete...
```

## Quickstart with Python

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/line-d-org/heroku-setup-py) or [view the repo on Github](https://github.com/line-d-org/heroku-setup-py)

This Python application creates an example workflow with two steps.

```python
# starter_workflow.py
import json
import os

import boto3

from utils import setup_s3_client


STARTER_WORKFLOW = {
    'title': 'Example 2-step workflow',
    'run': [
         {'cmd': """bash -c 'echo "Do Step 1"'""", 'machine': 'basic', 'no_output': True},
         {'cmd': """bash -c 'echo "Do Step 2"'""", 'machine': 'basic', 'no_output': True},
     ],
}


if __name__ == '__main__':
    s3 = setup_s3_client()

   # Upload the file to S3 and the workflow will start automatically
    s3.put_object(
        Body=json.dumps(STARTER_WORKFLOW).encode('utf-8'),
        Bucket=os.environ.get('LD_S3_BUCKET'),
        Key='in/example',
        Metadata={'ld_run': 'true'},
    )
```
You can start the workflow by running the script:

```term
$ python starter_workflow.py
```

## Setup S3 Client Dynamically (Recommended)

line^d uses temporary AWS credentials that are rotated every ~6 hours for enhanced security. We recommend loading your Heroku config dynamically to get the latest credentials on your local machine at run time. Here's an example using Python and the Heroku CLI:

```python
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


def setup_s3_client(local=False):
    if local:
        setup_local_env()

    aws = boto3.session.Session(
        aws_access_key_id=os.environ.get('LD_AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('LD_AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.environ.get('LD_AWS_SESSION_TOKEN'),
        region_name=os.environ.get('LD_REGION', 'us-east-1'),
    )
    return aws.client('s3')
```

## Setup Local Environment (Static)

After provisioning, you can replicate your `line_d` config locally for development environments.

Use the `local` [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) command to configure, run, and manage process types specified in your app's [Procfile](procfile). Heroku Local reads configuration variables from a `.env` file. Use `heroku config` to view an app's configuration variables in a terminal. Use the following command to add configuration variables to a local `.env` file:

```term
$ heroku config:get LD_AWS_ACCESS_KEY_ID -s  >> .env
$ heroku config:get LD_AWS_SECRET_ACCESS_KEY -s  >> .env
$ heroku config:get LD_AWS_SESSION_TOKEN -s  >> .env
$ heroku config:get LD_REGION -s  >> .env
```

> warning
> Don't commit credentials and other sensitive configuration variables to source control. In Git exclude the `.env` file with: `echo .env >> .gitignore`.

For more information, see the [Heroku Local](heroku-local) article.

## Defining Workflows in JSON

You can define workflows declaratively using JSON to support tasks written in any programming language. Here’s an example of a JSON file for a workflow.

```javascript
{
    'title': 'Workflow title',
    'run': [
        {
            'name': 'First task to run',
            'cmd': 'Heroku process name',
            'machine': 'dyno_size',
            'options': ['dir=out', 'model_preset=model-preset']
        },
        {
            'name': 'Run a parallel Task Group',
            'parallel': [
                {'cmd': 'get_data', 'machine': 'basic', 'options': ['endpoint=posts']},
                {'cmd': 'get_data', 'machine': 'basic', 'options': ['endpoint=users']},
                {'cmd': 'get_data', 'machine': 'basic', 'options': ['endpoint=comments']},
            ]
        },
    ]
}
```

### Workflow Format

|  Field Name  |  Type  | Required | Description |
| --- | --- | --- | --- |
|  `title` |  string  | Optional | Title of the workflow used for documentation and display
|  `run`  |  list of Tasks  | Required | The sequence of Tasks you want to run

### Task Format

|  Field Name  |  Type  | Required | Description |
| --- | --- | --- | --- |
|  `name` |  string  | Optional | The display name of the Task
|  `cmd`  | string  | Required | Heroku process to run that is defined in the Procfile
|  `machine`  | string  | Optional | Heroku Dyno size (default = 'basic')
|  `timeout`  | integer  | Optional | Seconds to wait for output before timing out (default = 60)
|  `options`  | list of strings  | Optional | Option name, value pairs to include in the Task environment vars - example: 'option_name=option_value'
|  `no_output`  | boolean  | Optional | Skip waiting for an output file. If the Task dyno starts up, it's considered successful. (default = False)
|  `wait_for`  | integer  | Optional | Seconds to wait after the Task completes (default = 0)

### Task Group Format

|  Field Name  |  Type  | Required | Description |
| --- | --- | --- | --- |
|  `name` |  string  | Optional | The display name of the Task Group
|  `parallel`  |  list of Tasks  | Required | Tasks you want to run in parallel (see format above)

## Runtime Environment Variables

line^d provides a set of helpful environment variables for each dyno at run time. Use the variable `line_D` to access them in JSON format.

## Managing Task Output and Status

By default, line^d expects each Task to send an output file as proof that it succeeded. You can disable this behavior by specifying the [`no_output` option](#task-format). Here's an example showing how to include the `task_id` with your output file:

```python
import json
import os

import boto3
import requests

from utils import setup_s3_client

def get_json():
    ld_env = json.loads(os.environ['line_D'])
    task_id = ld_env['task_id']
    url = 'https://jsonplaceholder.typicode.com/posts'
    resp = requests.get(url)
    records = resp.json() if resp.status_code == 200 else []

    # You have the option to store state to help with monitoring and composing workflows
    state = {
        'resp_status_code': resp.status_code,
        'num_records': len(records),
        'resp_time': str(resp.elapsed),
    }
    s3 = setup_s3_client()
    s3_client.put_object(
        Body=json.dumps(records).encode('utf-8'),
        Bucket=os.environ.get('LD_S3_BUCKET'),
        Key=f'out/{task_id}',
        Metadata={
            'ld_task_id': task_id,
            'ld_state': state,
    )

```

## Attach Workflows to Your Media and Data Files

It can be helpful to upload files with a post-processing workflow "attached" in one S3 request. This pattern can often eliminate the need for a separate background job system. Here’s an example of this pattern.

```python
import json
import os

import boto3

from utils import setup_s3_client

PROCESS_MEDIA = {
    'title': 'Process media files',
    'run': [
         {'cmd': 'process_image', 'machine': 'basic', 'timeout': 30},
     ],
}


if __name__ == '__main__':
    s3 = setup_s3_client()
    filename = 'example_img.jpg'
    example_file = open(filename, 'wb').close()
    with open(filename, 'rb') as media_f:
       # Use the S3 Metadata key "ld_code" to attach the workflow
        s3.put_object(
            Body=media_f,
            Bucket=os.environ.get('LD_S3_BUCKET'),
            Key=f'in/img/{filename}',
            Metadata={'ld_code': json.dumps(PROCESS_MEDIA)},
        )

```

## Monitoring Using the Dashboard

The line^d dashboard allows you to monitor your system activity. You can access the dashboard via the CLI:

```term
$ heroku addons:open line-d
Opening line-d for sharp-mountain-4005
```

or by visiting the [Heroku Dashboard](https://dashboard.heroku.com/apps) and selecting the application in question. Select **`line^d`** from the Add-ons menu.

## Dyno Startup Latency

The average latency between writing a file to S3 and dyno startup is **~7 seconds**. The total latency involves two main components:

* S3 event latency (~2 sec): time for S3 to deliver an event to the line^d compute engine
* Dyno start-up time (~5 sec): time for Heroku dynos to reach the `up` state after requesting it

>note
>Remember that latency can vary for many reasons, like network traffic, AWS or Heroku outages, etc. In those rare scenarios, latency at the 99 percentile could be many times greater than 7 seconds.

## Removing the Add-on

Before removing line^d, it's recommended to export your data from S3. Here is how to do that using the AWS CLI and the `sync` command:

```term
$ aws s3 sync s3://$LD_S3_BUCKET ./s3_export
download: s3://ld-private-cac9ba5f-8e42-436a-ac1d-e74708b0fddd/etl/users.json to s3_export/users.json
download: s3://ld-private-cac9ba5f-8e42-436a-ac1d-e74708b0fddd/etl/albums.json to s3_export/albums.json
download: s3://ld-private-cac9ba5f-8e42-436a-ac1d-e74708b0fddd/etl/posts.json to s3_export/posts.json
```

Then remove the add-on using the Heroku CLI.

> warning
> This action destroys all associated data and you can't undo it!

```term
$ heroku addons:destroy line-d
-----> Removing line-d-clear-41822 from example-app... done, v20 (free)
```

## Support

Submit all line^d support and runtime issues via one of the [Heroku Support channels](support-channels). Any non-support-related issues or product feedback is welcome at [support@line-d.net](mailto:support@line-d.net).