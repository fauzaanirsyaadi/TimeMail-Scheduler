# TimeMail-Scheduler
# Email Scheduler Web Application

This is a simple web application built with Python 3+ and Flask microframework to schedule and send emails at a later time.

## Features

- Provides a POST endpoint to save emails for a particular group of recipients with specified event ID, email subject, content, and timestamp.
- Emails are stored in a SQLite database.
- A script is included to periodically check the database for pending emails and send them at the specified timestamp.

## Requirement 
1. python 3 (this project use Python 3.12.2)
2. SQlite : https://www.sqlite.org/download.html
3. database client
4. code editor

## Installation

1. Clone the repository:

git clone https://github.com/fauzaanirsyaadi/TimeMail-Scheduler.git

2. Install dependencies:

pip install -r requirements.txt

3. Run the application:

python app.py