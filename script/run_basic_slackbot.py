import argparse
from slackbot.basic.igfbasicslackbot  import IgfBasicSlackBot

parser=argparse.ArgumentParser()
parser.add_argument('-s','--slack_config', required=True, help='Slack configuration json file')
parser.add_argument('-p','--project_data', required=True, help='Project data CSV file')
args=parser.parse_args()

slack_config=args.slack_config
project_data=args.project_data

try:
  igf_bot=IgfBasicSlackBot(slack_config_json=slack_config, \
                           project_data_file=project_data)
  igf_bot.start_igfslackbot()
except Exception as e:
  print(e)
