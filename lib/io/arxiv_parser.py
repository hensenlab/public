"""
Created on 2024

@author: B.J.Hensen, based on earlier work by N. Fiachi

This work is licensed under the GNU Affero General Public License v3.0

Copyright (c) 2024, Hensen Lab

All rights reserved.

See examples/check_new_arxiv_posts.py for usage.

"""

import logging
import time
import json
import urllib
import feedparser
import os.path

from datetime import datetime, timedelta, timezone
from unidecode import unidecode

def entry_to_string(entry):
    s = ''
    s += f'Title: {entry.title}\n' 
    s += f'Last Author: {entry.author}\n' 
    authors = ', '.join([a['name'] for a in entry.authors])
    s += f'Authors: {authors}\n'
    # par.append(f'arxiv-id: %s \n' % entry.id.split('/abs/')[-1])
    s += f'Link: {entry.link}\n'
    s += f'Updated: {entry.updated}\n'
    return s

def parse_list_of_names(names, send_message_func = None, sent_items_fp = None, wait_between_requests = 0.5, **kwargs):
    """
    
    for each entry in name_list, wheren an entry is a string with first and last name e.g. name_list = ['Markus Aspelmeyer','John D Teufel',]
    (copy the exact name from the autor in the author list as seen on arxiv, but without dots eg John D. Teufel is John D Teufel.) 
    parse the arxiv with args and kwargs pased on to parse_arxiv()
    
    Compile a short string that sumarizes the arxiv post and send it as an agument to send_message_func, 
    which is a function that should accept as a single argument a smessage string.
    
    """
    sent_items = []
    if sent_items_fp is not None:
        if os.path.exists(sent_items_fp):
            with open(sent_items_fp, 'rb') as f:
                sent_items = json.load(f)
    
    all_results = {}
    for name in names:
        results = parse_arxiv(name, **kwargs)
        all_results[name] = results
        
        for arxiv_id,entry in results.items():
            if arxiv_id in sent_items:
                logging.info(f'{name}: {arxiv_id} in results, but already sent')
                pass
            else:
                m = entry_to_string(entry)
                if send_message_func is not None:
                    send_message_func(m)
                logging.info(f'{name}: {arxiv_id} sending message')
                logging.debug(m)
                sent_items.append(arxiv_id)
        time.sleep(wait_between_requests)
    
    if sent_items_fp is not None:    
        if sent_items:
            with open(sent_items_fp, "w") as f:
                    json.dump(sent_items, f)   
            
    return all_results

def parse_arxiv(name, max_res = 5, max_days_old =1, newer_than = None):
    """
    Find the **max_res most recent arxiv posts with *name in the author list, and filter by being posted at most **max_days_old days ago.

    if a datetime **newer_than is supplied, use newer_than-timedelta(days = max_days_old) as a filter instead of now -timedelta(days = max_days_old)

    returns a dict of feedparser arxiv entries, with arxiv identifiers as keys

    """

    now = datetime.now().astimezone(timezone.utc)
    if newer_than is None:
        past_datetime = now - timedelta(days = max_days_old)
    else:
        past_datetime = newer_than - timedelta(days = max_days_old)
    logging.info(f'{now.strftime("%Y-%m-%d")}: checking post for {name} newer than {past_datetime.strftime("%Y-%m-%d %H:%M")}...')    
   
    results = {}
    
    # URL = d[name]
    names_split = name.split(' ')
    names_split.insert(0,names_split.pop(-1)) # put last name first
    # names_query = urllib.parse.quote('_'.join(names_split))
    
    names_query = unidecode('_'.join(names_split))
    
    URL =  f'http://export.arxiv.org/api/query?search_query=au:{names_query}&sortBy=lastUpdatedDate&sortOrder=descending&start=0&max_results={max_res:d}'
    logging.debug(URL)
    with urllib.request.urlopen(URL) as url:
        r = url.read()
        feed = feedparser.parse(r)
        for i,entry in enumerate(feed.entries):

            datetime_publish = datetime.fromisoformat(entry.updated)

            if  datetime_publish > past_datetime:
                arxiv_id = entry.id.split('/abs/')[-1]
                results[arxiv_id] = entry
            else:
                pass
    logging.info(f'Found {len(results)} new posts: ' + ', '.join(results.keys()))
            
    return results