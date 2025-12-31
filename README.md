# Klara Bot

Klara Bot is a Discord music bot built with Python using the `discord.py` library. It uses `yt-dlp` to stream audio from YouTube and other sources, and leverages a Redis queue to manage song requests. The entire application is containerized using Docker for easy setup and deployment. It also features a logging service that records song activity to a Neo4j graph database.

## Features

- **Music Playback**: Play audio from various online sources in a Discord voice channel.
- **Song Queue**: Add multiple songs to a queue.
- **Playback Control**: Pause, resume, skip, and stop the music.
- **Queue Management**: View the current queue and remove songs.
- **Repeat Mode**: Toggle repeating the current song.
- **Activity Logging**: Logs song additions and listening activity to a Neo4j database for analysis.

## Tech Stack

- **Bot Framework**: [discord.py](https://discordpy.readthedocs.io/en/stable/)
- **Audio Streaming**: [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- **Queue Management**: [Redis](https://redis.io/)
- **Database**: [Neo4j](https://neo4j.com/)
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
    Create a file named `.env.prod` in the root of the project and add your Discord bot token and Neo4j credentials:
    ```env
    DISCORD_TOKEN=your_discord_bot_token_here
    NEO4J_URI=bolt://your_neo4j_uri:7687
    NEO4J_USER=neo4j
    NEO4J_PASSWORD=your_neo4j_password
    ```

3.  **Run the bot:**
    Use Docker Compose to build and run the bot, Redis, and log service.
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
- `!play <query>`: Searches for a song and adds it to the queue. You can add multiple songs at once by separating queries with `;;`. If no query is provided, it plays the next song in the queue.
- `!skip`: Skips the current song.
- `!queue`: Displays the current song queue.
- `!current_song`: Shows the currently playing song.
- `!stop`: Stops the music and clears the queue.
- `!pause`: Pauses the current song.
- `!resume`: Resumes the paused song.
- `!remove <index>`: Removes a song from the queue at the specified position.
- `!repeat`: Toggles repeat mode for the current song.

## Makefile Commands

The project includes a `Makefile` with the following commands:

- `make run`: Runs the bot locally.
- `make run_logger`: Runs the log service locally.
- `make build`: Creates a zip archive of the bot for deployment.
- `make compose`: Builds and runs the Docker containers in detached mode.
- `make dev`: A convenience command for development, equivalent to `make compose`.

## Deployment

This project includes a GitHub Actions workflow for continuous deployment. When a pull request is merged into the `master` branch, the workflow automatically connects to the deployment server via SSH, pulls the latest changes, and restarts the Docker containers using the `make compose` command.

To enable this, you need to configure the following secrets in your GitHub repository settings (`Settings > Secrets and variables > Actions`):

- `SSH_HOST`: The hostname or IP address of your server.
- `SSH_USER`: The username for SSH login.
- `SSH_PRIVATE_KEY`: The private SSH key for authentication.
- `PROJECT_PATH`: The absolute path to the project directory on the server.