## Voice of America Swahili Scraper

This repo consists of a scraper for the Voice of America Swahili site and the scraped text upto 22nd June 2026. The main purpose is to build a text corpus for swahili. As stated in their terms of use: ```All text, audio and video material produced exclusively by the Voice of America is in the public domain. Credit for any use of VOA material should be given to voanews.com, Voice of America, or VOA. However, voanews.com content may also contain text, video, audio, images, graphics, and other copyrighted material that is licensed for use in VOA programming only. This material is not in the public domain and may not be copied, redistributed, sold, or published without the express permission of the copyright owner.```

## Structure

- Sentences in the ```sentences``` folder are the scraped sentences
- Sentences in the ```sentences_cleaned``` are the cleaned from the scraped text

 ## Scraping
 This was done daily using github actions that can be viewed on the ```.github/workflows``` folder. The daily scrap was saved in a csv file with the day's date. You can see the scraping script and cleaning script in the ```scripts``` folder. Scraping could be done manual on you machine using the ```manual_push.sh``` script. This was necessary also for testing the script on the main and can push the resulting code and sentences to github.

 ## Text normalization

 I also used my kiswahili text normalization library [https://github.com/bmwasaru/kiswahili-speech-normalization] to normalized the cleaned sentences into a single text file ```normalized_corpus/normalized_corpus.txt``` with metadata saved in the ```normalized_corpus/normalized_corpus.csv``` file.
 
 **Note**: The ```normalized_corpus/normalized_corpus.csv``` is too large (474MB) for Github so I ignored it in the ```.gitignore``` file. To generate it, run:

 ```python scripts/normalize_text.py sentences_cleaned normalized_corpus/normalized_corpus.csv --profile asr```
