# Zorak's Coding Challenge

Zorak's Coding Challenge is a series of 10 coding challenges, each with two parts, designed in the style of Advent of Code. This project is hosted on a Flask web application with a MongoDB database and is intended for members of the Practical Python Discord server. Completing both parts of each challenge grants access to a special discussion channel where participants can share their approaches and solutions.

**This project is currently a work in progress.**

## Features

- **Interactive Challenges**: Each challenge consists of two parts, allowing users to test their coding skills and problem-solving abilities with increasing difficulty.
- **Discord Integration**: Users can log in with their Discord accounts to track their progress and gain access to exclusive channels.
- **Progress Tracking**: The application tracks user progress, enabling them to see which challenges they have completed.
- **Obfuscation**: Challenge identifiers are obfuscated to add an extra layer of engagement and mystery.
- **Dynamic Content**: The challenges and their solutions are stored in a MongoDB database, allowing for easy updates and modifications.

## Getting Started

### Prerequisites

- Python 3.x
- Flask
- Flask-PyMongo
- Requests
- dotenv
- MongoDB

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/JefeThePug/Zorak-Coding-Challenges.git
   cd Zorak-Coding-Challenges
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the root directory and add your environment variables:
   ```
    SECRET_KEY=your_secret_key MONGO_URI=your_mongo_uri
    CLIENT_ID=your_discord_client_id
    CLIENT_SECRET=your_discord_client_secret
    BOT_TOKEN=your_discord_bot_token
   ```

4. Start the Flask application:
    ```bash
    python app.py
    ```

5. Open your browser and navigate to `http://127.0.0.1:5000` to access the application.

## Usage

- **Login**: Users can log in using their Discord accounts, which allows the application to track their progress.
- **Challenges**: Navigate to the challenges through the main page. Each challenge will have two parts that can be solved independently.
- **Submit Solutions**: Users can submit their answers for each part of a challenge. Correct answers will update their progress and grant access to the discussion channel.

## Code Overview

### Main Application (`app.py`)

The main application is built using Flask and includes the following key components:

- **Routes**: Various routes handle user authentication, challenge retrieval, and solution submission.
- **Database Integration**: MongoDB is used to store user progress, challenge data, and solutions.
- **Discord OAuth2**: The application uses Discord's OAuth2 for user authentication and role management.

### Client-Side Script (`ending.js`)

This script manages the display of end-of-challenge animations, utilizing the `confetti` library to create celebratory effects upon completing a challenge.


## License

This project is open-source and available for personal or educational use.

## Acknowledgments

- Inspired by [Advent of Code](https://adventofcode.com/)
- Built for the Practical Python Discord community
