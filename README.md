[line_d](https://elements.heroku.com/addons/line-d) (LD) helps you create powerful data lakes by bundling Amazon S3 storage with a Heroku Dyno compute engine. Trigger workflows whenever files are added to S3 using a declarative, JSON format.

## Provisioning the Add-on
```term
$ heroku addons:create line-d
Creating ADDON-SLUG on example-app... free
Your add-on has been provisioned successfully
```

## Getting Started (Python)

Deploy a Python application showing common use cases

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/line-d-org/heroku-setup-py)

```python
import json
import os

import boto3


STARTER_WORKFLOW = {
    'title': 'Example 2-step workflow',
    'run': [
         {'cmd': 'task_a', 'machine': 'basic', 'wait_for': 10, 'no_output': True},
         {'cmd': 'task_b', 'machine': 'basic', 'wait_for': 10, 'no_output': True},
     ],
}


if __name__ == '__main__':
    aws = boto3.session.Session(
        aws_access_key_id=os.environ.get('LD_AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('LD_AWS_SECRET_ACCESS_KEY'),
        aws_session_token=os.environ.get('LD_AWS_SESSION_TOKEN'),
        region_name='us-east-1',
    )
    s3 = aws.client('s3')

   # Upload the file to S3 and the workflow will start automatically
    s3_client.put_object(
        Body=json.dumps(STARTER_WORKFLOW).encode('utf-8'),
        Bucket=os.environ.get('LD_S3_BUCKET'),
        Key='in/example',
        Metadata={'ld_manage': 'true'},
    )
```

Add the following to your Heroku Procfile

```javascript
example_workflow: python workflow.py
task_a: echo "Running Task A"
task_b: echo "Running Task B"
```
Push your changes to Heroku

```term
$ git push heroku main
```
Run your workflow

```term
$ heroku run example_workflow
```


## Setup local environment dynamically (recommended)
line_d uses temporary AWS credentials (rotated every ~6 hours) for enhanced security. We recommend loading your Heroku Config dynamically to get the latest credentials on your local machine at run-time. Here is an example using Python and the Heroku CLI:

```python
import json
import os
import subprocess


def setup_local_env():
    """ Add Heroku Config variables to local environment """
    config_json = subprocess.check_output('heroku config -j', shell=True)
    heroku_env = json.loads(config_json)
    for k, v in heroku_env.items():
        os.environ[k] = v
```


## Setup local environment (static)
Once you've completed provisioning, you can replicate your line_d config locally for development environments.

Use the `local` [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) command to configure, run, and manage process types specified in your app's [Procfile](procfile). Heroku Local reads configuration variables from a `.env` file. Use `heroku config` to view an app's configuration variables in a terminal. Use the following command to add a configuration variable to a local `.env` file:

```term
$ heroku config:get ADDON-CONFIG-NAME -s  >> .env
```

> warning
> Don't commit credentials and other sensitive configuration variables to source control. In Git exclude the `.env` file with: `echo .env >> .gitignore`.

For more information, see the [Heroku Local](heroku-local) article.


## Defining workflows in JSON
Workflows are defined declaratively using JSON to support tasks written in any programming language.

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


### Workflow format

|  Field Name  |  Type  | Required | Description |
| --- | --- | --- | --- |
|  `title` |  string  | Optional | Title of the workflow used for documentation and display
|  `run`  |  list of Tasks  | Required | The sequence of Tasks you'd like to run

### Task format

|  Field Name  |  Type  | Required | Description |
| --- | --- | --- | --- |
|  `name` |  string  | Optional | Display name of the task
|  `cmd`  | string  | Required | Heroku process to run (defined in Procfile)
|  `machine`  | string  | Optional | Heroku Dyno size (default = 'basic')
|  `timeout`  | integer  | Optional | Seconds to wait for output before timing out (default = 60)
|  `options`  | list of strings  | Optional | Option name, value pairs to include in Task environment vars - example: 'option_name=option_value'
|  `no_output`  | boolean  | Optional | Skip waiting for an output file. If the Task Dyno starts up, it is considered successful. (default = False)
|  `wait_for`  | integer  | Optional | Seconds to wait after the Task completes (default = 0)

### Task Group format

|  Field Name  |  Type  | Required | Description |
| --- | --- | --- | --- |
|  `name` |  string  | Optional | Display name of the Task Group
|  `parallel`  |  list of Tasks  | Required | Tasks you'd like to run in parallel (see format above)


## Run-time environment variables
line_d provides a set of helpful environment variables for each Dyno at run-time. Use the variable `line_D` to access them (JSON formatted).


## Managing Task output and status

By default, line_d expects each Task to send an output file as proof that it succeeded. You may disable this behavior by specifying the `no_output` option (see above). Here is an example showing how to include the `task_id` with your output file:

```python
import json
import os

import boto3
import requests


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
    s3 = s3_client()
    s3_client.put_object(
        Body=json.dumps(records).encode('utf-8'),
        Bucket=os.environ.get('LD_S3_BUCKET'),
        Key=f'out/{task_id}',
        Metadata={
            'ld_task_id': task_id,
            'ld_state': state,
    )

```


## Attach workflows to your media/data files

It can be helpful to upload files with a post-processing workflow "attached" in one S3 request. This pattern can often eliminate the need for a separate background job system.

```python
import json
import os

import boto3


PROCESS_MEDIA = {
    'title': 'Process media files',
    'run': [
         {'cmd': 'process_image', 'machine': 'basic', 'timeout': 30},
     ],
}


if __name__ == '__main__':
    s3 = s3_client()
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


## Monitoring using the Dashboard

The line_d dashboard allows you to monitor your system and interactively develop workflows. You can access the dashboard via the CLI:

```term
$ heroku addons:open line-d
Opening line-d for sharp-mountain-4005
```

or by visiting the [Heroku Dashboard](https://dashboard.heroku.com/apps) and selecting the application in question. Select line-d from the Add-ons menu.


## Dyno startup latency
The average latency between writing a file to S3 and dyno startup is **~7 seconds**. The total latency involves two main components:

* S3 event latency (~2 sec) -- time for S3 to deliver an event to the line_d compute engine
* Dyno start-up time (~5 sec) -- time for Heroku Dynos to reach the `up` state once requested

>note
>Remember that latency can vary for many reasons, like network traffic, AWS or Heroku outages, etc. In those rare scenarios, latency at the 99 percentile could be many times greater than 7 seconds.

## Removing the Add-on

Remove line_d via the CLI:

> warning
> This action destroys all associated data and you can't undo it!

```term
$ heroku addons:destroy line-d
-----> Removing ADDON-SLUG from example-app... done, v20 (free)
```

Before removing line_d, export its data by [[describe steps if export is available]].

## Support

Submit all line_d support and runtime issues via one of the [Heroku Support channels](support-channels). Any non-support-related issues or product feedback is welcome at [[your channels]].