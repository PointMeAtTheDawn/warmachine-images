"""This converts a cardbundle.pdf (downloaded from Privateer Press) into
   Tabletop Simulator deck Saved Objects."""

import pickle
import os.path
import threading
import argparse
import PIL.ImageOps
from PIL import Image
from pdf2image import convert_from_path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def parse_images(fronts, backs, raw_page):
    """Chop a page from the PP PDF into its constituent card images."""
    fronts.append(raw_page.crop((94, 151, 592, 852)))
    fronts.append(raw_page.crop((597, 151, 1095, 852)))
    fronts.append(raw_page.crop((1099, 151, 1598, 852)))
    fronts.append(raw_page.crop((1602, 151, 2101, 852)))
    backs.append(raw_page.crop((94, 855, 592, 1553)))
    backs.append(raw_page.crop((597, 855, 1095, 1553)))
    backs.append(raw_page.crop((1099, 855, 1598, 1553)))
    backs.append(raw_page.crop((1602, 855, 2101, 1553)))


def drive_upload(image, name, links):
    """Upload a compiled TTS-compatible deck template image into Google Drive."""
    image.save(name)

    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    service = build("drive", "v3", credentials=creds)
    file_metadata = {"name": name}
    media = MediaFileUpload(name, mimetype="image/jpeg")
    file = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id")
        .execute()
    )

    media = MediaFileUpload(name, mimetype="image/jpeg")
    file = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id")
        .execute()
    )

    links[name] = "https://drive.google.com/uc?export=download&id=" + file.get("id")
    os.remove(name)


def package_pages(fronts, backs, page_count, links):
    """Stitch together card images into a TTS-compatible deck template image"""
    width = 410
    height = 585
    for i in range(page_count):
        fronts_image = Image.new("RGB", (4096, 4096))
        backs_image = Image.new("RGB", (4096, 4096))

        for j in range(70):
            if len(fronts) <= i * 70 + j:
                continue
            front = fronts[i * 70 + j].resize((width, height), Image.BICUBIC)
            back = backs[i * 70 + j].resize((width, height), Image.BICUBIC).rotate(180)
            fronts_image.paste(front, (j % 10 * width, (j // 10) * height))
            backs_image.paste(back, (j % 10 * width, (j // 10) * height))
        t_1 = threading.Thread(
            target=drive_upload, args=(fronts_image, f"f-{i}.jpg", links)
        )
        t_1.start()
        t_2 = threading.Thread(
            target=drive_upload, args=(backs_image, f"b-{i}.jpg", links)
        )
        t_2.start()
        t_1.join()
        t_2.join()


def write_deck(json, args, drive_links, num):
    """Craft the JSON for your final TTS deck Saved Object"""
    if args.name is None:
        args.name = "Warmachine"
    name = args.name + str(num)
    json = json.replace("DeckName", name)
    json = json.replace("FrontImageURL", drive_links[f"f-{num}.jpg"])
    json = json.replace("BackImageUrl", drive_links[f"b-{num}.jpg"])
    json = json.replace("ReplaceGUID", f"{name}C")
    json = json.replace("ReplaceGUID2", f"{name}D")
    if args.savedObjectsFolder is None:
        args.savedObjectsFolder = ""
    with open(args.savedObjectsFolder + name + ".json", "w") as deck:
        deck.write(json)


def convert():
    """This converts a cardbundle.pdf (downloaded from Privateer Press) into
       Tabletop Simulator deck Saved Objects."""
    parser = argparse.ArgumentParser(
        description="Convert Privateer Press card pdfs to Tabletop Simulator saved deck objects."
    )
    parser.add_argument(
        "-name",
        type=str,
        help="your deck name - possibly the faction you are converting",
    )
    parser.add_argument(
        "-savedObjectsFolder",
        type=str,
        help="your Saved Objects folder, include two trailing slashes cuz I am lazy.",
    )
    args = parser.parse_args()

    # Strip out the card images from the Privateer Press pdfs.
    card_fronts = []
    card_backs = []
    infile = "cardbundle.pdf"
    pages = convert_from_path(infile)
    for page in pages:
        parse_images(card_fronts, card_backs, page)

    # But we don't want the blank white cards.
    # I'd rather do a .filter, but I'm concerned a stray pixel would put them outta sync.
    filtered_fronts = []
    filtered_backs = []
    for i, card in enumerate(card_fronts):
        if PIL.ImageOps.invert(card).getbbox():
            filtered_fronts.append(card)
            filtered_backs.append(card_backs[i])

    # Collate the cards into the image format Tabletop Simulator requires.
    links = {}
    deck_count = len(card_fronts) // 70 + 1
    package_pages(filtered_fronts, filtered_backs, deck_count, links)

    # And let's shove em all in your Saved Objects folder :)
    deck_json = ""
    with open("decktemplate.json", "r") as deck_template:
        deck_json = deck_template.read()
    for i in range(deck_count):
        write_deck(deck_json, args, links, i)


if __name__ == "__main__":
    convert()
