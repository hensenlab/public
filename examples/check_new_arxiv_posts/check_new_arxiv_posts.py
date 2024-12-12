"""
Created 2024

@author: B.J.Hensen

This work is licensed under the GNU Affero General Public License v3.0

Copyright (c) 2024, Hensen Lab

All rights reserved.

Use e.g. Windows Task Scheduler to run this periodically (under actions add "wscript path_to_here/check_new_arxiv_posts.vbs, adapt the paths in that file too.)

"""
import logging
import os.path

import config
from lib.io import slack_message_sender
from lib.io import arxiv_parser

from arxiv_list_of_names import names



max_day_old=7

logging_fp = os.path.join(config.get_config_folder(),'arxiv_post_logger.log')
sent_items_fp = os.path.join(config.get_config_folder(),'arxiv_post_sent_items.json')

logging.basicConfig(filename=logging_fp, level=logging.INFO)

all_results = arxiv_parser.parse_list_of_names(names,
                                               send_message_func = slack_message_sender.send_slack_message_to_arxiv_channel,
                                               sent_items_fp = sent_items_fp, 
                                               max_days_old = max_day_old)
    


         
       
        