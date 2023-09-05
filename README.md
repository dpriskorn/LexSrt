# LexSrt
The purpose of this script is to get all the senses for all the words in a SRT-file from Wikidata

It uses SpaCy to tokenize each subtitle in the srt and looks up the corresponding lexeme in 
Wikidata based on the detected position of speech and token representation.

# Example subtitle Ice Age
![image](https://github.com/dpriskorn/LexSrt/assets/68460690/5e864721-b62d-40ba-b638-3001d15e3669)

The script encourages the user to contribute to Wikidata if 
senses are completely missing like in this case with https://www.wikidata.org/wiki/Lexeme:L333957.

# License
GPLv3+
