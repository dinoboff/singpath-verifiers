# singpath-verifiers

The docker-based verifiers that support SingPath.com


## Requires

- python2.7;
- bash;
- git;
- docker;
- docker-machine;
- a Firebase DB and its secret.
- Either VirtualBox or an account on a provider
[docker-machine support](https://docs.docker.com/machine/drivers/os-base/)
(e.g.: Digital Ocean, Amazon Web Services or Google Compute Engine)

On OS X and Windows, you should install
[Docker Tools](https://www.docker.com/docker-toolbox); it will include
docker, docker-machine and VirtualBox.

On Windows, install git usually include a bash terminal.


## Setup

We will setup a machine named "default" on a virtualbox VM and configure
verifier to run on it.

1. create the docker host : `docker-machine create -d virtualbox default`;
2. checkout the verifier repository: `git clone https://github.com/ChrisBoesch/singpath-verifiers.git`;
3. configure docker: `eval "$(docker-machine env default)"`;
4. configure the verifier for this machine: `cd singpath-verifiers; ./bin/verifier init`;
5. upload the rules (WIP: The rules are not yet public).

TODO: publish rules or partial rules related to rules.


## Running the verifier

0. start the machine if it's not already running: `docker-machine start default`
1. configure docker: `eval "$(docker-machine env default)"`
2. start the verifier: `cd singpath-verifiers; ./bin/verifier start default`
   The first time it will need download the base images and build the verifier
   images without a cache; it will take a few minutes.
3. press "ctrl+c" to stop the verifier.
4. Either stop the machine (`docker-machine stop default`) or restart the
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
a `verify` files in a `verifier/verifiers/dummy` directory:

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

You would also need to add the image to `verifier/images.json`:
```json
{
    "java": {
        "name": "singpath/verifier2-java",
        "path": "./verifier/verifiers/java"
    },
    "javascript": {
        "name": "singpath/verifier2-javascript",
        "path": "./verifier/verifiers/javascript"
    },
    "python": {
        "name": "singpath/verifier2-python",
        "path": "./verifier/verifiers/python"
    },
    "dummy": {
        "name": "singpath/verifier2-dummy",
        "path": "./verifier/verifiers/dummy"
    }
}

```

To try it with:
```shell
docker run -ti --rm singpath/verifier2-dummy:latest verify '{
	"tests": "",
	"solution": "print(\"TODO\")"
}'
```

or:
```shell
./bin/verifier test dummy '{
	"tests": "",
	"solution": "print(\"TODO\")"
}'
```



## Pushing task to the queue


E.g. Pushing two tasks to the queue the default machine setting is targeting:

```shell
./bin/verifier push default '---
language: java
tests: |
  SingPath sp = new SingPath();
  assertEquals(4.0, sp.add(2.0, 2.0));
solution: |
  public class SingPath {

    public Double add(Double x, Double y) {
      return x + y;
    }
  }
---
language: java
tests: |
  SingPath sp = new SingPath();
  assertEquals(2.0, sp.echo(2.0));
solution: |
  public class SingPath {
    public Double echo(Double x) {
      return x;
    }
  }
'
```

Or to push a file content, you could use:
```shell
./bin/verifier push default "$(< ./some-file.yaml)"
```

You can use yaml (must start with "---") to push one or many document at once
or json to encode the payload. Yaml is easier to use when writing
blocks (using "|") of text.


The push command will send to
"https://your-firebase-idfirebaseio.com/singpath/queues/my-queue/tasks/some-task-id":
```
{
	"payload": {
		"language": "java",
		"tests": "...",
		"solutions": "..."
	},
	"owner": "defaul-pusher-user",
	"started": false,
	"completed": false,
	"archived": false
}
```

To push a file content, you could use:
```shell
./bin/verifier push default "$(< ./some-file.yaml)"
```

## TODO

- setup [circleci.com](https://circleci.com/docs/docker) continuous tests.
- clean up after failing or exiting verifier worker.
- implement python and javascript verifier (simply switch the current verifiers server
  api for a cli).
- Build language verifier from daemon container.