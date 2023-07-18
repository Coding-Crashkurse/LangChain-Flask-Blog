# Auto Article Poster

This project revolves around the automation of creating and posting articles. Utilizing various Python scripts and functionalities, it provides an efficient solution for automatic content generation and delivery.

## Project Components

1. **app.py**:
   This is the main script for running the Flask application. It serves as the central hub for our application, managing all routes and functionalities. It connects to our PostgreSQL database and initiates the web application's routes. Here, the user can view the list of articles, access individual articles, and create new articles.

2. **create_real_article.py**:
   This script is used for generating and inserting articles into the database. It uses the GPT-4 language model to generate articles based on a list of predefined topics. These generated articles are then inserted into the database. The script is designed to be run in a scheduled manner, allowing for consistent content generation.

3. **Docker files**:
   There are two Dockerfiles: Dockerfile_app and Dockerfile_cron. Dockerfile_app is responsible for setting up the environment for running the Flask application, including installing all the necessary dependencies. Dockerfile_cron, on the other hand, is designed to set up a cron job for running the create_real_article.py script on a scheduled basis.

4. **docker-compose.yaml**:
   This file manages the orchestration of our Docker services. It defines and configures the application's services according to our specifications, facilitating the running of our application in a contained environment.

5. **crontab**:
   This file holds the schedule for running our create_real_article.py script. By configuring this file, we can control how often new articles are generated and inserted into the database.

6. **requirements.txt**:
   This file lists all the Python dependencies required for our application to run. These dependencies are installed in the Docker containers during setup.

7. **templates**:
   This directory holds all the HTML templates used by our Flask application. These templates define the structure and appearance of the web pages in our application.
