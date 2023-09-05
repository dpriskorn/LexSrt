"""
Copyright 2023 Dennis Priskorn
start time 0210
The purpose of this script is to get all the senses for all the words in a SRT-file from Wikidata
Limitations:
* hardcoded to english
* if multiple LIDs are returned from WDQS skip them
"""
import logging

import config
from models import LexSrt

logging.basicConfig(level=config.loglevel)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting")
    ls = LexSrt()
    ls.start()
