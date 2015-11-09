# singpath-verifiers

The docker-based verifiers that support SingPath.com

You can launch an Amazon Linux image on EC2 to quickly test all the current
verifiers. The following steps need to be run after you launch a starndare
Amazon micro-instance image.

```shell
sudo yum install docker
sudo service docker start
docker run -ti --rm \
	-v /var/run/docker.sock:/var/run/docker.sock \
	--group-add 100 \
	-e SINGPATH_FIREBASE_SECRET="firebase-secret" \
	-e SINGPATH_FIREBASE_QUEUE="https://singpath.firebaseio.com/singpath/queues/my-queue" \
	singpath/verifier2
```


The verifier will create a Firebase auth token using a Firebase secret if you
are administrator of the Firbase db. If you don't, the verifier will query a
auth token from an authentication server using a SingPath token (TODO, the
token will be available from SingPath.com for authorized users).

The verifier will watch for new task of Firebase queue, attempt to claim them
(you can have a cluster competing for the tasks), run the tests in a one use
container and save the result.


## Developing verifier.

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

It may log debug info to `stderr`.

These results from verifying code are usually used to build a table to provide
feedback to users:

```
| Called | Expected | Recieved  | Correct |
| ------ |:--------:| :--------:|:--------|
| x      | 2        | 2         | True    |
| y      | 3        | 2         | False   |
```

A dummy verifier would add a  `Dockerfile` and a `verify` files to a
`dummy` directory:
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

You should also need to add the image to `verifier/src/images.json`:
```json
{
    "java": "singpath/verifier2-java",
    "javascript": "singpath/verifier2-javascript",
    "python": "singpath/verifier2-python",
    "dummy": "singpath/verifier2-dummy"
}
```

The verifier daemon and verify images are built automatically via the master
branch gets new commits using docker hub automatic build.
