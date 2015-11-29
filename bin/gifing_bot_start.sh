#!/bin/bash

# Name of the application
NAME="the_gifing_bot"

# Project directory (contains the actual application that we're going to run)
SERVERDIR=/home/jeremy/apps/TheGIFingBot/

# Virtual environment directory
VENVDIR=/home/jeremy/Envs/the_gifing_bot

# the user and group the program should run as
USER=jeremy
GROUP=jeremy

# Activate the virtual environment
source $VENVDIR/bin/activate

# Append the server directory to our python path environment variable.
export PYTHONPATH=$SERVERDIR:$PYTHONPATH

# Programs meant to be run under supervisor should not daemonize themselves
# (do not use --daemon). So we'll cd to our server directory and then
# execute the program using the virtualenv's version of python.
cd $SERVERDIR
exec $VENVDIR/bin/python gifing_bot.py
