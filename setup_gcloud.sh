#!/bin/bash

# Install the Google Cloud SDK
sudo apt-get update && sudo apt-get install -y apt-transport-https ca-certificates gnupg
# Check if the source list already exists before adding
if ! grep -q "^deb .*cloud.google.com/apt" /etc/apt/sources.list /etc/apt/sources.list.d/*; then
  echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
  curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
fi
sudo apt-get update && sudo apt-get install -y google-cloud-sdk

# Ensure the .config/gcloud directory has the correct permissions and no directory conflicts
mkdir -p /home/gitpod/.config/gcloud
sudo chown -R gitpod:gitpod /home/gitpod/.config