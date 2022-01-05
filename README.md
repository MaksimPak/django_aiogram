# Django + aiogram bot combination

This software combines the use of django admin and bot. The bot handles user interaction in telegram while admin is used for controlling purposes

# How to use

Copy the project, create .env file, and enter the .env.example file variables.

Once required vars are filled, run docker compose up, and it will start local web server for django admin.
In order to run bot, you will need to enter docker container, go to src folder and run python -m bot [polling/webhook]
