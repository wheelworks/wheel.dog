FROM alpine:3.3

RUN apk add --no-cache socat
CMD socat -d -d TCP-LISTEN:8080,fork UNIX:/var/run/docker.sock
