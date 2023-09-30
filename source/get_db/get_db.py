import argparse
import os
import pickle

import newspaper
import pytz
import yaml
from tchan import ChannelScraper

utc = pytz.UTC

def parse_paper(link: str, db: dict):
    """
    Parse the article using the link: extract text, meta-keywords, authors, site name and twitter acc.
    :param link: link to the article
    :param db: dict with the inidial meta
    :return: updated dict
    """
    article = newspaper.Article(link)
    article.download()
    article.parse()
    target_fields = ['source_url', 'text', 'meta_keywords', 'authors']
    for target_field in target_fields:
        if target_field in article.__dict__.keys():
            db[target_field] = article.__dict__[target_field] if article.__dict__[target_field] else float('nan')
    if 'site_name' in article.meta_data['og'].keys():
        db['site_name'] = article.meta_data['og']['site_name']
    else:
        db['site_name'] = db['channel']
    try:
        db['twitter'] = article.meta_data['twitter']['site']
    except:
        db['twitter'] = float('nan')
    return db

def scrape_info(source: str, no_of_msgs=10, path_to_db="data/db/demhack_db.p", path_to_errors="data/db/demhack_errors.p"):
    """
    This function extracts information from the last no_of_msgs telegram posts from the source telegram channel
    :param out_folder: absolute path to the output folder
    :param source: telegram channel name
    :param no_of_msgs: number of messages you want to parse
    :return:
    """
    if not os.path.exists(os.path.dirname(path_to_db)):
        os.makedirs(os.path.dirname(path_to_db))
    if not os.path.exists(os.path.dirname(path_to_errors)):
        os.makedirs(os.path.dirname(path_to_errors))
    if os.path.exists(path_to_db):
        with open(path_to_db,"rb") as f:
            db = pickle.load(f)
    else:
        db = list()
    scraper = ChannelScraper()
    errors = list()
    try:
        for idx, msg in enumerate(scraper.messages(source)):
            if (idx < no_of_msgs):
                msg_url = f'https://t.me/{msg.channel}/{msg.id}'
                if not msg_url in [existed_msgs['type'] for existed_msgs in db]: # check if a msg is already in db
                    target_info = {'created_at': msg.created_at,
                                   'message_url': f'https://t.me/{msg.channel}/{msg.id}',
                                   'type': msg.type,
                                   'channel': msg.channel,
                                   'edited': msg.edited,
                                   'url': dict(msg.urls)['link'] if 'link' in dict(msg.urls).keys() else float('nan'),
                                   'author': msg.author,
                                   'tg_preview_text': msg.text,
                                   'source_url': float('nan'),
                                   'text': float('nan'),
                                   'meta_keywords': float('nan'),
                                   'authors': float('nan'),
                                   'twitter': float('nan'),
                                   'site_name': float('nan')}
                    if isinstance(target_info['url'], str): # if the full-text-link available
                        target_info = parse_paper(target_info['url'], target_info) # extract info from the article
                    db.append(target_info)
            else:
                pickle.dump(db, open(path_to_db, "wb")) # write everything to the db
                return
    except:
        errors.append((source))
        if len(errors) >= no_of_msgs:
            pickle.dump(errors, open(path_to_errors, "wb"))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get N last messages from the source telegram channels')
    parser.add_argument('--config', type=str, required=True,
                        help='Path to the yaml file with the "source" key and telegram channels names as values')
    parser.add_argument('--no_of_msgs', default=5, type=int, required=True,
                        help='Number of message you want to extract from the each source listed in the config file')
    parser.add_argument('--path_to_db', type=str, required=True,
                        help='Absolute path to the database (pickle), e.g. /$(pwd)/data/db/demhack_db.p')
    parser.add_argument('--path_to_errors', type=str, required=True,
                        help='Absolute path to the error-logs (pickle), e.g. $(pwd)/data/db/demhack_errors.p')
    args = parser.parse_args()

    with open(args.config) as config_file:
        sources = yaml.safe_load(config_file)['sources']

    for source in sources:
        scrape_info(source=source, no_of_msgs=args.no_of_msgs, path_to_db=args.path_to_db,
                    path_to_errors=args.path_to_errors)
