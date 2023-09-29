import argparse
import glob
import os
import pickle
import re

import pytz
from tchan import ChannelScraper
import yaml

utc = pytz.UTC


def scrape_info(source: str, no_of_msgs: int, path_to_db: str, path_to_errors: str):
    """
    This function extracts information from the last no_of_msgs telegram posts from the source telegram channel
    :param source: tg channel name
    :param no_of_msgs: number of messages you want to parse
    :param path_to_db: absolute path to the output db
    :param path_to_errors: absolute path to the error-logs
    :return:
    """
    if not os.path.exists(os.path.dirname(path_to_db)):
        os.makedirs(os.path.dirname(path_to_db))
    if not os.path.exists(os.path.dirname(path_to_errors)):
        os.makedirs(os.path.dirname(path_to_errors))
    if os.path.exists(path_to_db):
        with open(path_to_db, "rb") as f:
            db = pickle.load(f)
    else:
        db = list()
    scraper = ChannelScraper()
    errors = list()
    batches = glob.glob(f'{os.path.dirname(path_to_db)}/{source}_batch_idx*.p')
    batch_idx = max(
        (int(re.sub('.*_', '', re.findall('batch_idx_[\d]*', db)[0])) for db in batches)) + 1 if batches else 0
    try:
        for idx, msg in enumerate(scraper.messages(source)):
            if idx < no_of_msgs:
                if not msg.id in [existed_msgs.id for existed_msgs in db]:
                    db.append(msg)
            else:
                pickle.dump(path_to_db, open(f"{os.path.dirname(path_to_db)}/{source}_batch_idx_{batch_idx}.p", "wb"))
                pickle.dump(db, open(path_to_db, "wb"))
                return
    except:
        errors.append((source, batch_idx))
        if len(errors) >= no_of_msgs:
            pickle.dump(errors, open(path_to_errors, "wb"))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get N last messages from the source telegram channels')
    parser.add_argument('--config', type=str, required=True,
                        help='Path to the yaml file with the "source" key and telegram channels names as values')
    parser.add_argument('--no_of_msgs', type=int, required=True)
    parser.add_argument('--path_to_db', type=str, required=True,
                        help='data/db/demhack_db.p')
    parser.add_argument('--path_to_errors', type=str, required=True,
                        help='data/db/demhack_errors.p')
    args = parser.parse_args()

    with open(args.config) as config_file:
        sources = yaml.safe_load(config_file)['sources']

    for source in sources:
        scrape_info(source=source, no_of_msgs=args.no_of_msgs, path_to_db=args.path_to_db,
                    path_to_errors=args.path_to_errors)
