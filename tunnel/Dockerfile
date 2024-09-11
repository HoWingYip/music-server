FROM alpine:latest

RUN apk update && apk add --no-cache jq curl
RUN curl https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz | tar xzvf - -C /usr/local/bin

CMD ["ngrok", "tcp", "2222"]
