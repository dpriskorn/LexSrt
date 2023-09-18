"""These are from
https://github.com/fnielsen/ordia/blob/db4af5029044f5010204ec6516549ccb318dc259/ordia/query.py
Author: Finn Nielsen
License: Apache 2.0, see https://github.com/fnielsen/ordia/blob/master/LICENSE

The code was improved to use WikibaseIntegrator for
better error handling and standardization"""
import logging
from functools import lru_cache
from typing import Optional

import requests
from spacy.tokens import Token
from wikibaseintegrator.wbi_helpers import execute_sparql_query  # type: ignore

from models.exceptions import MissingInformationError

logger = logging.getLogger(__name__)


def escape_string(string):
    r"""Escape string to be used in SPARQL query.

    Parameters
    ----------
    string : str
        String to be escaped.

    Returns
    -------
    escaped_string : str
        Escaped string.

    Examples
    --------
    >>> escape_string('"hello"')
    '\\"hello\\"'

    >>> escape_string(r'\"hello"')
    '\\\\\\"hello\\"'

    """
    return string.replace("\\", "\\\\").replace('"', r"\"")


@lru_cache(maxsize=1048)
def iso639_to_q(iso639):
    """Convert ISO 639 to Wikidata ID.

    Convert an ISO 639-1 or ISO 639-2 identifier to the associated Q
    identifier by a lookup with the Wikidata Query Service.

    Parameters
    ----------
    iso639 : str
        ISO 639 identifier as a string.

    Returns
    -------
    q : str
        String with Wikidata ID. It is empty if the code is not found.

    Examples
    --------
    >>> iso639_to_q('en') == 'Q1860'
    True

    >>> iso639_to_q('xnx') == ''
    True

    >>> iso639_to_q('dan') == 'Q9035'
    True

    """
    if len(iso639) == 2:
        property = "wdt:P218"
    elif len(iso639) == 3:
        property = "wdt:P219"
    else:
        raise ValueError("Wrong length of `iso639`")

    query = 'SELECT ?code WHERE {{ ?code {property} "{iso639}" }}'.format(
        property=property, iso639=escape_string(iso639)
    )

    url = "https://query.wikidata.org/sparql"
    params = {"query": query, "format": "json"}
    response = requests.get(
        url,
        params=params,  # headers=HEADERS,
        # Arbitrary set timeout to please bandit
        timeout=10,
    )
    data = response.json()

    bindings = data["results"]["bindings"]
    if bindings:
        return bindings[0]["code"]["value"][31:]
    else:
        return ""


@lru_cache(maxsize=1048)
def spacy_token_to_forms(
    token: Optional[Token] = None,
    lookup_proper_noun_as_noun: bool = False,
    lookup_proper_noun_as_adjective: bool = False,
    overwrite_as_noun: bool = False,
    overwrite_as_verb: bool = False,
    overwrite_as_adjective: bool = False,
):
    """Identify Wikidata lexeme from spaCy token.

    Parameters
    ----------
    token : spacy.tokens.token.Token

    Returns
    -------
    lexemes : list of strings

    Examples
    --------
    >>> class Token(object):
    ...     pass
    >>> token = Token()
    >>> setattr(token, 'lang_', 'da')
    >>> setattr(token, 'norm_', 'biler')
    >>> setattr(token, 'pos_', 'NOUN')
    >>> spacy_token_to_forms(token)
    ['L36385']

    """
    POSTAG_TO_Q = {
        "ADJ": "Q34698",
        "ADV": "Q380057",
        "INTJ": "Q83034",
        "NOUN": "Q1084",
        "PROPB": "Q147276",
        "VERB": "Q24905",
        "ADP": "Q134316",
        "AUX": "Q24905",
        "CCONJ": "Q36484",
        "DET": "Q576271",
        "NUM": "Q63116",
        "PART": "Q184943",
        "PRON": "Q36224",
        "PROPN": "Q147276",
        "SCONJ": "Q36484",
    }
    if not token:
        raise MissingInformationError()
    if lookup_proper_noun_as_noun:
        POSTAG_TO_Q["PROPN"] = "Q1084"
    if lookup_proper_noun_as_adjective:
        POSTAG_TO_Q["PROPN"] = "Q34698"
    if overwrite_as_noun:
        token.pos_ = "NOUN"
    if overwrite_as_verb:
        token.pos_ = "VERB"
    if overwrite_as_adjective:
        token.pos_ = "ADJ"
    if token.pos_ in ["PUNCT", "SYM", "X"]:
        logger.error(f"PoS '{token.pos_}' is a punctuation, skipping")
        return []
    # Cleaning
    if '"' in token.norm_:
        token.norm_ = token.norm_.replace('"', "")
    if "-" in token.norm_:
        token.norm_ = token.norm_.replace("-", "")
    # logger.info(f"token.norm_: {token.norm_}")
    # exit()

    iso639 = token.lang_
    logger.info(f"Detected iso639 language: {iso639}")
    language = iso639_to_q(iso639)
    logger.debug(f"Matched language to the following QID: {language}")
    # if lowercase:
    #     representation = token.norm_.lower()
    # else:
    representation = token.norm_
    if token.pos_ not in POSTAG_TO_Q:
        logger.error(f"PoS '{token.pos_}' not supported, skipping")
        return []
    lexical_category = POSTAG_TO_Q[token.pos_]
    logger.info(
        f"Trying to match token with the representation "
        f"'{representation}' and lexical category "
        f"'{lexical_category}' with Wikidata"
    )
    query = """
       SELECT DISTINCT ?form {{
           ?lexeme dct:language wd:{language} ;
            wikibase:lexicalCategory / wdt:P279* wd:{lexical_category} ;
            ontolex:lexicalForm ?form.
            ?form ontolex:representation "{representation}"@{iso639} .
    }}""".format(
        language=language,
        lexical_category=lexical_category,
        representation=representation,
        iso639=iso639,
    )

    logger.debug("Looking up in Wikidata")
    from wikibaseintegrator.wbi_config import config as wbi_config  # type: ignore

    wbi_config["USER_AGENT"] = "LexSrt/1.0 (https://www.wikidata.org/wiki/User:So9q)"
    data = execute_sparql_query(query=query)
    bindings = data["results"]["bindings"]
    if bindings:
        forms = [binding["form"]["value"][31:] for binding in bindings]
        return forms
    else:
        return []
