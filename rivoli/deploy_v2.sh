cd rivoli-bot
pip3 install --target . -r rivoli/requirements.txt
zip -r9 function.zip .
aws lambda update-function-code --function-name rivoliBotV2 --zip-file fileb://function.zip --profile perso
rm function.zip