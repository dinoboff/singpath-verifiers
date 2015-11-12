FROM node:4.2-slim

# Dockert client will connect via '/var/run/docker.sock' by default.
# The socket should be pass via `-v /var/run/docker.sock:/var/run/docker.sock`.
# If you need to use the remote api via HTTP(S) instead, you should pass the 
# docker host address by setting a container environment variable with 
# `-e SINGPATH_DOCKER_HOST=$DOCKER_HOST`.
# Your remote docker host most likely requires SSL client authentication. 
# The verifier will expect them in "/cert". You should mount the with
# `-v $DOCKER_CERT_PATH:/cert:ro`.
ENV SINGPATH_DOCKER_HOST="" 
ENV SINGPATH_DOCKER_CERT_PATH="/cert"

ENV SINGPATH_FIREBASE_SECRET=""
ENV SINGPATH_FIREBASE_QUEUE="https://singpath-play.firebaseio.com/singpath/queues/default"
ENV SINGPATH_PUSH_USER_ID="#1"

# Update npm, the docker client (for developpement) and create expected folders.
RUN npm install npm -g && \
	npm -v && \
	curl -SL -O https://get.docker.com/builds/Linux/x86_64/docker-1.9.0 && \
	chmod +x docker-1.9.0 && \
	mv docker-1.9.0 /usr/local/bin/docker && \
	mkdir -p /app && \
	mkdir -p $SINGPATH_DOCKER_CERT_PATH \
	mkdir -p /app/bin

ENV PATH="$PATH:/app/bin"

# Install the app dependencies.
WORKDIR /app
COPY ./package.json /app/package.json
RUN npm install && \
	npm cache clean

RUN adduser --system verifier
USER verifier

# Add the rest of the app files.
COPY ./src /app/src
COPY ./tests /app/tests
COPY ./bin /app/bin
COPY images.json .eslintrc solution-example.yaml README.md CONTRIBUTING.md /app/

LABEL com.singpath.verifier="master"

CMD ["/app/bin/verifier"]
