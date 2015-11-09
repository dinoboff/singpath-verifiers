# Verifier for SingPath.com

Pull verifier task from a Firebase queue and run them inside container.

## Usage

A verifier container need the socket to the docker daemon, read/write access to
it and the Firebase secret. By default, the socket group is "docker" and
assuming the docker group ID was 100, to run verifier watching the default
queue, you would start the docker image with this command:

```shell
docker run -ti --rm \
	-v /var/run/docker.sock:/var/run/docker.sock \
	--group-add 100 \
	-e SINGPATH_FIREBASE_SECRET="firebase-secret" \
	singpath/verifier2
```

To target a different queue:

```shell
docker run -ti --rm \
	-v /var/run/docker.sock:/var/run/docker.sock \
	--group-add 100 \
	-e SINGPATH_FIREBASE_SECRET="firebase-secret" \
	-e SINGPATH_FIREBASE_QUEUE="https://singpath-play.firebaseio.com/singpath/queues/my-queue" \
	singpath/verifier2
```

### Group ID

To find the group ID to add:
- on OS X or windows, connect to the docker host: `docker-machine ssh default`.
- check the group assigned to `/var/run/docker.sock`: `ls -l /var/run/docker.sock.
- find the group id in `/etc/group`: cat /etc/group

On docker-machine hosts, the group id should be "100".

### TODO

- add support for Firebase Auth token directly instead of a Firebase secret.
