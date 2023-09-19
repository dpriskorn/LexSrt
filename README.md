# LexSrt
This tool helps language mentors overview all lexeme forms found in sentences or SRT-files.

It uses SpaCy to tokenize each subtitle in the srt and looks up the corresponding lexeme in 
Wikidata based on the detected position of speech and token representation.

The CLI script encourages the user to contribute to Wikidata if 
senses are completely missing on the matched lexemes.

The API does not check if senses exists in Wikidata currently and 
simply does the cleaning and matching and output the result.

# Features
* API to match a sentence to lexeme forms
* CLI to analyze a SRT-file and get an overview
  of all lexemes an their senses and get 2 csv output files with details

# Limitations
* Only languages with a spaCy model are currently supported

# Installation
1. Clone the repository.
2. Install dependencies using Poetry:
```sh
poetry install
```
3. Install a language model for spaCy, for example:
```sh
poetry run python3 -m spacy download en_core_web_sm
```

## Recommended models
These models are recommended over the standard spaCy ones in https://spacy.io/models
* sv: https://github.com/Kungbib/swedish-spacy <- Note 800 MB download

# Use
## CLI
```sh
python cli.py -i path-to-srt.srt --lang en --spacy_model en_core_web_sm
```

You can fiddle with the configuration options in `config.py`

## API
An API using fastapi has been implemented.

It supports 2 fields sent via a HTTP POST request:
* spacy_model
* sentence

After installing Uvicorn, you can start the API in debug mode:
```sh
uvicorn api:app --reload
```

Test it with:
```sh
curl -X POST -H "Content-Type: application/json" http://localhost:8000/process_sentence \
     -d '{"spacy_model": "en_core_web_sm", "sentence": "This is a test sentence."}' 
```

It should output something like:
```json
{
  "data": [
    {
      "token": "This",
      "spacy_pos": "PRON",
      "matched_forms": [
        "L643260-F1"
      ]
    },
    {
      "token": "is",
      "spacy_pos": "AUX",
      "matched_forms": [
        "L1883-F4"
      ]
    },
    {
      "token": "a",
      "spacy_pos": "DET",
      "matched_forms": [
        "L2767-F1"
      ]
    },
    {
      "token": "test",
      "spacy_pos": "NOUN",
      "matched_forms": [
        "L220909-F1"
      ]
    },
    {
      "token": "sentence",
      "spacy_pos": "NOUN",
      "matched_forms": [
        "L6117-F1"
      ]
    },
    {
      "token": ".",
      "spacy_pos": "ADJ",
      "matched_forms": []
    }
  ]
}
```
  

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
* FastAPI is super duper nice and chatgpt supports it well so using it is a breeze.
