#! /bin/bash

# script directory https://stackoverflow.com/a/246128
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

cd "$DIR"
if [ ! -d lib/waveshare_epd ]; then
  if [ ! -f waveshare-e-Paper.zip ]; then
    echo getting e-Paper archive
    wget -qO waveshare-e-Paper.zip https://github.com/waveshare/e-Paper/archive/master.zip
  fi
  echo unpacking e-Paper archive
  mkdir ziptmp
  unzip -q -d ziptmp  waveshare-e-Paper.zip
  mv ziptmp/e-Paper-master/RaspberryPi_JetsonNano/python/lib .
  rm -r ziptmp
fi

if [ "$1" == "install" ]; then
  if [ `whoami` != "root" ]; then
    echo must be root.  run '"'sudo setup.sh install'"' instead
    exit 1
  fi
  default_port=80
  default_device=epd2in13b_V3
  echo -n "port (default: ${default_port})? "
  read port
  if [ -z "$port" ]; then
    port=$default_port;
  fi
  echo -n "device (default: ${default_device})? "
  read device
  if [ -z "$device" ]; then
    device=$default_device;
  fi
  echo "Installing systemd unit with --port=${port} --device=${device}"
  echo generating /usr/bin/einklightswitch.sh
  echo "cd \"$DIR\" && exec python3 main.py --port=\"${port}\" --device=\"${device}\"" > /usr/bin/einklightswitch.sh
  echo copying einklightswitch.service systemd unit
  cp einklightswitch.service /lib/systemd/system
  echo "starting service..."
  sudo systemctl start einklightswitch
  echo "enabling service to start at boot"
  sudo systemctl enable einklightswitch
fi
