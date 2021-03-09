if [ "$(id -u)" != "0" ]; then
  echo '[Error]: You must run this setup script with root privileges.'
  echo
  exit 1
fi
apt-get update
apt-get -y install python3-pip
apt-get -y install default-jre
git submodule init
git submodule update
pip3 install -e .
