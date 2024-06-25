#execute this only after you have the momentum docker image ready
#you need to have google default application credentials set up
#this script is targetted at macOs & linux support, where the default location of adc is
# ~/.config/gcloud/application_default_credentials.json , however, feel free to modify this path
# if you're on windows, the path likely is %appdata%/gcloud/application_default_credentials.json

export ADC=~/.config/gcloud/application_default_credentials.json

docker run \
--env-file .env \
-e GOOGLE_APPLICATION_CREDENTIALS=/tmp/keys/application_default_credentials.json \
-v ${ADC}:/tmp/keys/application_default_credentials.json:ro \
-p 8001:8001 \
momentum