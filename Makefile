default: build

build:
	docker build -t singpath/verifier2:latest ./verifier
	docker build -t singpath/verifier2-java:latest ./java
	docker build -t singpath/verifier2-python:latest ./python
	docker build -t singpath/verifier2-javascript:latest ./javascript
.PHONY: build