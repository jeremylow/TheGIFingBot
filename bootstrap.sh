#!/usr/bin/env bash

apt-get update
apt-get -y upgrade
apt-get install -y git
apt-get install -y python-pip
apt-get install -y python-virtualenv
apt-get install -y python-dev
sudo pip install virtualenvwrapper
ln -fs /usr/share/virtualenvwrapper/virtualenvwrapper.sh /usr/bin/virtualenvwrapper.sh
apt-get install -y imagemagick
add-apt-repository -y ppa:mc3man/trusty-media
apt-get update
apt-get install -y ffmpeg
apt-get install -y rabbitmq-server

#############################

rm -rf ~/Envs
mkdir ~/Envs
cd ~/Envs
virtualenv --no-site-packages gifingbot --python=/usr/bin/python3
cd /vagrant
source ~/Envs/gifingbot/bin/activate
