import os,re
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from igf_data.task_tracking.igf_slack import IGF_slack
from igf_data.utils.fileutils import get_temp_dir

class IgfBasicSlackBot:
  '''
  A basic slack bot for IGF specific operations
  
  required params:
  slack_config_json: A json file containing slack api keys
  project_data_file: A csv file containing project data
  
  usage:
    - create bot
        bot=IgfBasicSlackBot(slack_config_json, project_data_file)
    - start bot
        bot.start_igfslackbot()
  '''
  def __init__(self,slack_config_json, project_data_file):
    self.project_data_file=project_data_file
    self.igf_slack=IGF_slack(slack_config=slack_config_json)                    # create slack client instance


  @staticmethod
  def _get_project_status(project_igf_id,data_file,output_file):
    '''
    A static method for fetching project status
    
    required params:
    project_igf_id: A project igf id
    data_file: A csv file containing project data
    output_file: An output png filepath
    '''
    try:
      message=None
      data=pd.read_csv(data_file)
      data=data[data['project_igf_id']==project_igf_id]
      if len(data.index) >0:
        data=data.groupby(['sample_igf_id','seqrun_igf_id']).sum()
        data=data.reset_index(level=['seqrun_igf_id'])
        fig, ax=plt.subplots()
        ax=sns.barplot(data=data,\
                       y='attribute_value',\
                       x=data.index,\
                       hue='seqrun_igf_id')
        #ax.legend(bbox_to_anchor=(1.8, 1))
        plt.xticks(fontsize=8,rotation=30)
        plt.savefig(output_file)
      else:
        message='project id {0} not found'.format(project_igf_id)
      return output_file, message
    except:
      raise

  @staticmethod
  def _calculate_reply(user_input,project_data):
    '''
    A static method for calculation reply for the user input
    
    required params:
    user_input: A user input string from slack message
    project_data: A project data csv file
    '''
    try:
      file_plot=None
      pattern=re.compile(r'^<@\w+>(\s+)?(\S+)(\s+)?:(\s+)?(\S+)$')
      m = re.search(pattern,user_input)
      if m:
        key=m.group(2)
        value=m.group(5)
        if key.lower()=='project':
          tmp_dir=get_temp_dir()
          file_plot, msg=_get_project_status(project_igf_id=value,\
                                            data_file=project_data,\
                                            output_file=os.path.join(tmp_dir,'project_data.png'))
        else:
          msg='No option present for keyword {0}, available options are: project'.\
              format(key)
      else:
        msg='No match found, available options are: project'
      return file_plot,msg
    except:
      raise

  @staticmethod
  def _parse_slack_output(slack_rtm_output, bot_id, channel_id):
    '''
    A static method for parsing slack realtime output
    
    required_params:
    slack_rtm_output: slack realtime stream
    bot_id: slack bot id
    channel_id: slack channel id
    '''
    try:
      if isinstance(slack_rtm_output, list) and \
         len(slack_rtm_output) > 0:
        for output in slack_rtm_output:
          if output and \
             'text' in output and \
             '@'+bot_id in output['text'] and \
             channel_id in output['channel']:
            yield output
    except:
      raise

  def start_igfslackbot(self):
    '''
    A method for starting Basic slackbot
    '''
    try:
      igf_slack=self.igf_slack
      if igf_slack.slackobject.rtm_connect():
        while True:
          for output in self._parse_slack_output(slack_rtm_output=igf_slack.slackobject.rtm_read(),
                                                 bot_id=igf_slack.slack_bot_id, 
                                                 channel_id=igf_slack.slack_channel_id):
            file_plot,message=self._calculate_reply(user_input=output['text'],self.project_data_file)
            if message is None:
              igf_slack.post_file_to_channel(filepath=file_plot,
                                             thread_ts=output['ts'])
            else:
              igf_slack.post_message_to_channel_thread(message=message,
                                                       thread_id=output['ts'])
    except KeyboardInterrupt:
      print('Stopped bot')
    except:
      raise
