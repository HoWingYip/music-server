# SSH music server

This is a tool for downloading music and syncing it across multiple devices. It consists of an SSH server, SSH tunnel, and Telegram bot. If you have your own internet-facing domain, the tunnel is not required.


## Contents
- [In short](#in-short)
- [Configuration](#configuration)
  - [SSH server](#ssh-server)
  - [SSH tunnel](#ssh-tunnel)
  - [Telegram bot](#telegram-bot)
- [Using the Telegram bot](#using-the-telegram-bot)


## Usage overview

1. Install Docker
2. Configure settings
3. On server: `cd music-server && docker compose up`
4. Download songs through Telegram bot
5. On client: `rsync -avz user@remote:/music/ /your/local/music/dir`


## Configuration

First ensure Docker is installed. Then configure settings by setting environment variables in the following files:
- `server/.env.server` for SSH server
- `tunnel/.env.tunnel` for SSH tunnel
- `telegram_bot/.env.bot` for Telegram bot

Finally, in the project root directory, run `docker compose up --build`.

### SSH server

We use the [`linuxserver/openssh-server`](https://hub.docker.com/r/linuxserver/openssh-server) Docker image. Environment variables go in `server/.env.server`. Available settings are listed [here](https://hub.docker.com/r/linuxserver/openssh-server). Below is an example config:

```bash
# User ID and group ID of SSH user
PUID=1000
PGID=1000

# Server timezone
TZ=Etc/UTC+0

# Folder containing SSH public keys to accept
PUBLIC_KEY_DIR=/config/pub_keys

# Enable/disable password access
PASSWORD_ACCESS=false

# Username of SSH user
USER_NAME=user

# Whether SSH user should be sudo
SUDO_ACCESS=false

# Log to stdout instead of file
LOG_STDOUT=true
```

### SSH tunnel

The author tunnels SSH traffic over an ngrok TCP tunnel because she's poor. Should you choose to do the same, you'll need an ngrok account with a valid payment method added. (ngrok TCP tunnels are free-of-charge as of 21 Sep 2024, but they require a payment method for abuse prevention.)

Setup is simple. In `tunnel/.env.tunnel`, set `NGROK_AUTHTOKEN=your_ngrok_authtoken`.

If you're hosting your music on an internet-facing server, the SSH tunnel is not necessary. To disable it, comment out the following sections in `compose.yml`:
- `services.ssh-tunnel`
- `services.telegram-bot.depends_on`

### Telegram bot

In `telegram_bot/.env.bot`, set:

```bash
BOT_TOKEN=your_bot_token # Telegram bot token
ALLOWED_USER_IDS=1,2,3 # comma-separated list of Telegram user IDs to allow
```

## Using the Telegram bot


