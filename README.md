# singpath-verifiers

The docker-based verifiers that support SingPath.com


## Requires

- python2.7;
- bash;
- git;
- docker;
- docker-machine;
- Either VirtualBox or an account on a provider
[docker-machine support](https://docs.docker.com/machine/drivers/os-base/)
(e.g.: Digital Ocean, Amazon Web Services or Google Compute Engine)

On OS X and Windows, you should install
[Docker Tools](https://www.docker.com/docker-toolbox).


## Setup

We will setup a machine named "default" on a virtualbox VM and configure
verifier to run on it.

1. create the docker host : `docker-machine create -d virtualbox default`
2. checkout the verifier repository: `git clone https://github.com/ChrisBoesch/singpath-verifiers.git`
3. configure docker: `eval "$(docker-machine env default)"`
4. configure the verifier for this machine: `cd singpath-verifiers; ./bin/verifier init`


## Running the verifier

1. start the machine: `docker-machine start default`
2. configure docker: `eval "$(docker-machine env default)"`
3. start the verifier: `cd singpath-verifiers; ./bin/verifier start default`
   The first time it will need download the base images and build the verifier
   images without a cache; it will take a few minutes.
 4. press "ctrl+c" to stop the verifier.
 5. Either stop the machine (`docker-machine stop default`) or restart the
    verifier [3].

The verifier will create a Firebase auth token using a Firebase secret if you
are administrator of the Firbase db. If you are not administrator, the verifier
will instead query a auth token from an authentication server using a SingPath
token (Not implemented yet, the token will be available from SingPath.com for
authorized users).

The verifier will watch for new task in the Firebase queue, attempt to claim
them (you can have a cluster competing for the tasks), run the tests in a one
use container and save the result).


## Language verifier

A language verifier image should have a command named "verify" in the path taking
a json encoded "solution" and "tests" payload as argument and return to `stdout`
the json encode result object. It must have a boolean "solved" field; typically
something like this:

```json
{"results": [{"call": "x", "expected": 2, "received": "2", "correct": True},
             {"call": "y", "expected": 3, "received": "2", "correct": False}],
"printed": ",
"solved": False,}
```

These results from verifying code are usually used to build a table to provide
feedback to users:

```
| Called | Expected | Recieved  | Correct |
| ------ |:--------:| :--------:|:--------|
| x      | 2        | 2         | True    |
| y      | 3        | 2         | False   |
```

It can also log debug info to `stderr`. The `stderr` stream will be piped to
the verifier daemon `stderr`.


### Example

A new verifier, that we would name `dummy`, would have a `Dockerfile` and
a `verify` files in a `dummy` directory:

```Dockefile
FROM python:3.4-slim

RUN mkdir -p /app && adduser --system verifier

ENV PATH="$PATH:/app"
COPY verify /app/
RUN chmod +x /app/verify

```

```python
#!/usr/bin/env python3

import sys
import json

print(sys.argv, file=sys.stderr)
json.dump({
    "solved": False,
    "errors": "Not implemented.",
}, fp=sys.stdout)

```

And you would build the container image with:
```shell
cd ./dummy
docker build -t singpath/verifier2-dummy:latest .
```

To try it:
```shell
docker run -ti --rm singpath/verifier2-dummy:latest verify '{
	"tests": "",
	"solution": "print(\"TODO\")"
}'
```

You would also need to add the image to `images.json`:
```json
{
    "java": "singpath/verifier2-java",
    "javascript": "singpath/verifier2-javascript",
    "python": "singpath/verifier2-python",
    "dummy": "singpath/verifier2-dummy"
}
```


## Pushing task to the queue

A task body should have a payload, an owner and all flags set to false:
```
{
	"payload": {
		"language": "java",
		"tests": "...",
		"solutions": "..."
	},
	"owner": "user-auth-id",
	"started": false,
	"completed": false,
	"archived": false
}
```

It should be saved at
"https://your-firebase-idfirebaseio.com/singpath/queues/my-queue/tasks/some-task-id".

TODO: add command to push the task.


## TODO

- setup [circleci.com](https://circleci.com/docs/docker) continuous tests.
- clean up after failing or exiting verifier worker.
- implement python and javascript (simply switch the current verifiers server
  api for a cli).
