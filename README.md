# LexSrt
The purpose of this script is to get all the senses for all the words in a SRT-file from Wikidata

It uses SpaCy to tokenize each subtitle in the srt and looks up the corresponding lexeme in 
Wikidata based on the detected position of speech and token representation.

The script encourages the user to contribute to Wikidata if 
senses are completely missing on the matched lexemes.

# Limitations
* Only languages with a spaCy model are currently supported
* No API

# Installation
Clone the repository.

## Recommended models
These models are recommended over the standard spaCy ones in https://spacy.io/models
* sv: https://github.com/Kungbib/swedish-spacy

# Use
`python main.py -i path-to-srt.srt`

You can fiddle with the configuration options in `config.py`

# Examples
## Ice Age with english limit 8
![image](https://github.com/dpriskorn/LexSrt/assets/68460690/f07d14a4-45cb-45cb-a617-889604652639)

## Life of Brian english limit 11
matches:
![image](https://github.com/dpriskorn/LexSrt/assets/68460690/78408744-0827-426c-837a-3e6fc1960336)
match errors:
![image](https://github.com/dpriskorn/LexSrt/assets/68460690/3c8b2f1f-645a-4502-8486-c5a9a0012d3c)

## Shrek norwegian limit 9
matches:
![image](https://github.com/dpriskorn/LexSrt/assets/68460690/3679cd0f-b6f9-4436-9ff1-195a80b75fc7)
match errors:
![image](https://github.com/dpriskorn/LexSrt/assets/68460690/5e704b47-3cc9-453d-8765-e8154fda360f)

# License
GPLv3+ with the exeption of the code borrowed from Ordia, see the licens in the file.

# Thanks
Big thanks to [Finn Nielsen](https://www.wikidata.org/wiki/Q96296336) for writing the spaCy->lexeme function. 
I improved it a bit for my purposes to get what I wanted.

# What I learned
* Having your own classes is nice. 
* Reusing easy to read quality code from others is nice
* Reusing classes from other projects is nice
* WBI is still lacking convenince methods I want so I'll
propose them to be included upstream to make life easier for others.
* Pydantic and black goes a long way, I don't really need all the other linting mypy stuff for whipping up working code like this in a few hours. Stability is good enough for me with those two and the inspection in PyCharm.
