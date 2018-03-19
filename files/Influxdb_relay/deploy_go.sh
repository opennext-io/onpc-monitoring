#!/bin/bash
pushd /opt
  wget -P /opt/ https://dl.google.com/go/go1.10.linux-amd64.tar.gz
  tar  -xzf /opt/go1.10.linux-amd64.tar.gz -C /opt/
popd
pushd /usr/local/bin
  find /opt/go/bin/ -type f -exec ln -sf {} \;
popd
if ! grep -qw 'GOROOT="/opt/go"' /etc/environment; then
  echo 'GOROOT="/opt/go"' | tee -a /etc/environment
fi