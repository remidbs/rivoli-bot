# RivoliBot

Compute tweets based on relevant facts of daily records of the number of cyclists passing by a counter.

Example usage for the counter in rue de Rivoli in Paris: https://twitter.com/RivoliBot

## Usage

### Example

```sh
git clone git@github.com:remidbs/rivoli-bot.git
cd rivoli-bot
python3 rivoli/tweet.py -i rivoli/tests/test_data/rivoli_test_data.csv -d random -o STD
```

### Example output

```
Le 07/12/2019, il y a eu 6 896 passages de cyclistes.
4ème meilleur jour historique.
```

### General usage

```
git clone git@github.com:remidbs/rivoli-bot.git
cd rivoli-bot
python3 rivoli/tweet.py


usage: tweet.py [-h] --output {STD,TWITTER,SLACK} [--target-day TARGET_DAY]
                --input-filename INPUT_FILENAME
                [--twitter-customer-api-key TWITTER_CUSTOMER_API_KEY]
                [--twitter-customer-api-secret_key TWITTER_CUSTOMER_API_SECRET_KEY]
                [--twitter-access-token TWITTER_ACCESS_TOKEN]
                [--twitter-access-token-secret TWITTER_ACCESS_TOKEN_SECRET]
                [--slack-url SLACK_URL]

arguments
  -h, --help            show the help message and exit
  --output {STD,TWITTER,SLACK}, -o {STD,TWITTER,SLACK}
        Where to dispatch the computed tweet.
        STD for printing result to standard output
        TWITTER for tweeting results (requires API keys below)
        SLACK for posting result to slack (requires SLACK_URL below)

  --target-day TARGET_DAY, -d TARGET_DAY optional
        last, random or date in format DD/MM/YYYY. Default to last
        Target day for computing the tweet.
        'last' for using last available day
        'random' for using a random day among available days
        date in format DD/MM/YYYY

  --input-filename INPUT_FILENAME, -i INPUT_FILENAME
        CSV filename containing counter data.
        File format: No header, 2 columns:
        - date in DD/MM/YYYY format
        - count (int)

  --twitter-customer-api-key TWITTER_CUSTOMER_API_KEY optional
        Along with next arguments, API keys for posting tweet.
        (Can be set in config.py once and for all, along with --counter argument)
  --twitter-customer-api-secret_key TWITTER_CUSTOMER_API_SECRET_KEY optional
  --twitter-access-token TWITTER_ACCESS_TOKEN optional
  --twitter-access-token-secret TWITTER_ACCESS_TOKEN_SECRET optional

  --slack-url SLACK_URL optional
        Slack url for posting tweet to slack if chosen output is SLACK
```

## Referenced usages

<table>
  <tr>
    <th>Location</th>
    <th>URL</th>
  </tr>
  <tr>
    <td>Rue de Rivoli, Paris</td>
    <td>https://twitter.com/RivoliBot</td>
  </tr>
  <tr>
    <td>Rue de Sebastopol, Paris</td>
    <td>https://twitter.com/SebastopolBot</td>
  </tr>
</table>

Feel free to add your own.
