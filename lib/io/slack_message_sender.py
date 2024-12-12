"""
Created on 2024

@author: B.J.Hensen

This work is licensed under the GNU Affero General Public License v3.0

Copyright (c) 2024, Hensen Lab

All rights reserved.
"""

import requests


""" To make the slack message sending work see https://api.slack.com/start/overview#installing_distributing.
1. create a slack app and add it to a workspace (or use the existing python_message_bot, living in the hensenlab Workspace, see https://api.slack.com/apps)
2. Under the app features, activate Incoming Webhooks, if it is not yet activated
3. Then add a Webhook URL to the workspace with the "Add New Webhook To Workspace" button. This
   will ask you to select a channel to post incoming messages into. Copy the url and paste as webhook_url below.
4. profit.

"""

def send_slack_message_to_arxiv_channel(message):
    webhook_url = 'https://hooks.slack.com/services/XXXXXXXXXXX/XXXXXXXXXXX/XXXXXXXXXXXXXXXXXXXXXXXX' #arxiv channel
    requests.post(webhook_url, json={'text': message})
