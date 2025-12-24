# Klara Bot

Klara Bot is a Discord music bot built with Python using the `discord.py` library. It uses `yt-dlp` to stream audio from YouTube and other sources, and leverages a Redis queue to manage song requests. The entire application is containerized using Docker for easy setup and deployment.

## Features

- **Music Playback**: Play audio from various online sources in a Discord voice channel.
- **Song Queue**: Add multiple songs to a queue.
- **Playback Control**: Pause, resume, skip, and stop the music.
- **Queue Management**: View the current queue and remove songs.
- **Repeat Mode**: Toggle repeating the current song.

## Tech Stack

- **Bot Framework**: [discord.py](https://discordpy.readthedocs.io/en/stable/)
- **Audio Streaming**: [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- **Queue Management**: [Redis](https://redis.io/)
- **Containerization**: [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/)
- **CI/CD**: [GitHub Actions](https://github.com/features/actions)

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd klara-bot
    ```

2.  **Create an environment file:**
    Create a file named `.env.prod` in the root of the project and add your Discord bot token:
    ```env
    DISCORD_TOKEN=your_discord_bot_token_here
    ```

3.  **Run the bot:**
    Use Docker Compose to build and run the bot and the Redis service.
    ```bash
    docker compose up --build
    ```
    To run in the background, use:
    ```bash
    docker compose up -d --build
    ```

## Bot Commands

- `!join`: Joins the voice channel you are in.
- `!leave`: Leaves the voice channel.
- `!play <query>`: Searches for a song and adds it to the queue. If no query is provided, it plays the next song in the queue.
- `!skip`: Skips the current song.
- `!queue`: Displays the current song queue.
- `!stop`: Stops the music and clears the queue.
- `!pause`: Pauses the current song.
- `!resume`: Resumes the paused song.
- `!remove <index>`: Removes a song from the queue at the specified position.
- `!repeat`: Toggles repeat mode for the current song.

## Deployment

This project includes a GitHub Actions workflow for continuous deployment. When a pull request is merged into the `master` branch, the workflow automatically connects to the deployment server via SSH, pulls the latest changes, and restarts the Docker containers using the `make compose` command.

To enable this, you need to configure the following secrets in your GitHub repository settings (`Settings > Secrets and variables > Actions`):

- `SSH_HOST`: The hostname or IP address of your server.
- `SSH_USER`: The username for SSH login.
- `SSH_PRIVATE_KEY`: The private SSH key for authentication.
- `PROJECT_PATH`: The absolute path to the project directory on the server.
