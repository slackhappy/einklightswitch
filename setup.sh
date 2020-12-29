#! /bin/bash

if [ ! -f  waveshare-e-Paper.zip ]; then
  echo getting e-Paper archive
  wget -qO waveshare-e-Paper.zip https://github.com/waveshare/e-Paper/archive/master.zip
fi

if [ ! -d lib ]; then
  echo unpacking e-Paper archive
  mkdir ziptmp
  unzip -q -d ziptmp  waveshare-e-Paper.zip
  mv ziptmp/e-Paper-master/RaspberryPi_JetsonNano/python/lib .
  rm -r ziptmp
fi

