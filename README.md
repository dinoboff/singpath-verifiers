# singpath-verifiers

The docker-based verifiers that support SingPath.com

You can launch an Amazon Linux image on EC2 to quickly test all the current
verifiers. The following steps need to be run after you launch a standard
Amazon micro-instance image.

```shell
# install docker
sudo yum install docker
sudo service docker start

# Get the ID of the group having write access on the docker socket
export DOCKER_GROUP_NAME=`ls -l /var/run/docker.sock | awk '{ print $4 }'`
export DOCKER_GROUP_ID=`cat /etc/group | grep "^$DOCKER_GROUP_NAME" | cut -d: -f3`

# Start the verifier, passing the socket and giving it read/write permission
docker run -ti --rm \
	-v /var/run/docker.sock:/var/run/docker.sock \
	--group-add $DOCKER_GROUP_ID \
	-e SINGPATH_FIREBASE_SECRET="your-firebase-secret" \
	-e SINGPATH_FIREBASE_QUEUE="https://singpath.firebaseio.com/singpath/queues/my-queue" \
	singpath/verifier2
```

The verifier will create a Firebase auth token using a Firebase secret if you
are administrator of the Firbase db. If you are not administrator, the verifier
will instead query a auth token from an authentication server using a SingPath
token (Not implemented yet, the token will be available from SingPath.com for
authorized users).

The verifier will watch for new task in the Firebase queue, attempt to claim
them (you can have a cluster competing for the tasks), run the tests in a one
use container and save the result).

	Note:

	The `--group-add $DOCKER_GROUP_ID` need to be adjusted to the host. It
	should the GID off the docker socket host.

	The GID is `100` for the OS X / Windows docker virtual machine.


## Development

To build the verifier images locally:
```shell
git clone https://github.com/dinoboff/singpath-verifiers.git
cd singpath-verifiers
make
```

A verifier container should have command name "verify" in the path taking
a json encoded "solution" and "tests" payload as argument and return to `stdout`
the json encode result object. It must have a boolean "solved" field; typically
something like this:

```json
{'results': [{'call': 'x', 'expected': 2, 'received': '2', 'correct': True},
             {'call': 'y', 'expected': 3, 'received': '2', 'correct': False}],
'printed': '',
'solved': False,}
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

A new verifier, that we name `dummy` would have a `Dockerfile` and a `verify`
files in a `dummy` directory:

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

You would also need to add the image to `verifier/images.json`:
```json
{
    "java": "singpath/verifier2-java",
    "javascript": "singpath/verifier2-javascript",
    "python": "singpath/verifier2-python",
    "dummy": "singpath/verifier2-dummy"
}
```

And add a line to `Makefile` (Makefile must use TAB for indentation):
```Makefile
default: build

build:
	docker build -t singpath/verifier2:latest ./verifier
	docker build -t singpath/verifier2-java:latest ./java
	docker build -t singpath/verifier2-python:latest ./python
	docker build -t singpath/verifier2-javascript:latest ./javascript
	docker build -t singpath/verifier2-dummy:latest ./dummy
.PHONY: build
```

The verifier daemon and verify images are built automatically when the master
branch gets new commits using docker hub automatic build.

## TODO

- setup Travis [circleci.com](https://circleci.com/docs/docker) test.
- clean up after failing or exiting verifier worker.
- implement python and javascript (simply switch the current verifiers server
  api for a cli).
- Update document to setup
