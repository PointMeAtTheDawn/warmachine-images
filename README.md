# Warmachine Image Parser

This turns a cardbundle.pdf (downloaded from Privateer Press' Card DB, placed in the same directory as the repository) into a series of images you can upload to use in Tabletop Simulator Warmachine decks, with the backs right-side up. 

Prerequisites:
* [Python](https://www.python.org/downloads/)
* [Poppler - Windows](http://blog.alivate.com.au/poppler-windows/) / [Poppler - All](https://poppler.freedesktop.org/)
* Modules: `pip install -r requirements.txt`

Usage:
`python convert.py`

Note: there's a hecka lotta commented out code in there that used to automatically upload the images to various places and then generate the Tabletop Simulator deck jsons and inject them into your Saved Objects folder for a 1-step process. Unfortunately, I couldn't figure out how to get Imgur to stop forcibly downscaling the image resolutions to illegible quality, Google Drive is incompatible with Tabletop Simulator for Reasons™ (bug Berserk to fix this in http://www.berserk-games.com/forums/showthread.php?7711-Attempt-to-load-undefined-image-extensions-in-cache-like-you-already-do-for-URLs), and I didn't quickly find documentation on how to upload to your own Steam Cloud via API, so I'm gonna leave this here for now. PRs or feedback welcome.