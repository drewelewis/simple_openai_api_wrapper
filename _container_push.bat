@echo off
REM Set your Docker Hub username and image name
set IMAGE_NAME=simpleopenaiapiwrapper
set TAG=latest
set DOCKERHUB_USER=drewl

docker login --username %DOCKERHUB_USER%

REM Tag the image for Docker Hub
docker tag %IMAGE_NAME%:%TAG% %DOCKERHUB_USER%/%IMAGE_NAME%:%TAG%

REM Push the image to Docker Hub
docker push %DOCKERHUB_USER%/%IMAGE_NAME%:%TAG%