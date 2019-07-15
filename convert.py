"""This converts a cardbundle.pdf (downloaded from Privateer Press) into
   Tabletop Simulator deck Saved Objects."""

import os
import argparse
import json
import threading
from shutil import copyfile
import PIL.ImageOps
from PIL import Image
import cloudinary.uploader
import cloudinary.api
from pdf2image import convert_from_path

def parse_images(fronts, backs, raw_page):
    """Chop a page from the PP PDF into its constituent card images."""
    # 400 DPI
    # fronts.append(raw_page.crop((188, 303, 1185, 1703)))
    # fronts.append(raw_page.crop((1193, 303, 2190, 1703)))
    # fronts.append(raw_page.crop((2199, 303, 3196, 1703)))
    # fronts.append(raw_page.crop((3205, 303, 4201, 1703)))
    # backs.append(raw_page.crop((188, 1709, 1185, 3106)))
    # backs.append(raw_page.crop((1193, 1709, 2190, 3106)))
    # backs.append(raw_page.crop((2199, 1709, 3196, 3106)))
    # backs.append(raw_page.crop((3205, 1709, 4201, 3106)))
    # 200 DPI
    fronts.append(raw_page.crop((94, 151, 592, 852)))
    fronts.append(raw_page.crop((597, 151, 1095, 852)))
    fronts.append(raw_page.crop((1099, 151, 1598, 852)))
    fronts.append(raw_page.crop((1602, 151, 2101, 852)))
    backs.append(raw_page.crop((94, 855, 592, 1553)))
    backs.append(raw_page.crop((597, 855, 1095, 1553)))
    backs.append(raw_page.crop((1099, 855, 1598, 1553)))
    backs.append(raw_page.crop((1602, 855, 2101, 1553)))
    # 150 DPI
    # fronts.append(page.crop((70,114,444,639)))
    # fronts.append(page.crop((447,114,821,639)))
    # fronts.append(page.crop((824,114,1198,639)))
    # fronts.append(page.crop((1202,114,1576,639)))
    # backs.append(page.crop((70,641,444,1165)))
    # backs.append(page.crop((447,641,821,1165)))
    # backs.append(page.crop((824,641,1198,1165)))
    # backs.append(page.crop((1202,641,1576,1165)))

def load_config():
    """Load your config"""
    with open('config.json') as json_file:
        data = json.load(json_file)
        cloudinary.config(
            cloud_name=data["cloud_name"],
            api_key=data["api_key"],
            api_secret=data["api_secret"]
        )
        return data["width"], data["height"], data["saved_objects_folder"]

def image_upload(name, links):
    """Upload a compiled TTS-compatible deck template image into Cloudinary."""

    res = cloudinary.uploader.upload(name)

    links[name] = res["url"]
    os.remove(name)
    print(links[name])


def package_pages(cards_width, cards_height, fronts, backs, page_count, links):
    """Stitch together card images into a TTS-compatible deck template image"""
    pixel_width = 4096//cards_width
    pixel_height = 4096//cards_height
    for i in range(page_count):
        fronts_image = Image.new("RGB", (4096, 4096))
        backs_image = Image.new("RGB", (4096, 4096))

        for j in range(cards_width * cards_height):
            if len(fronts) <= i * cards_width * cards_height + j:
                continue
            front = fronts[i * cards_width * cards_height + j].resize(
                (pixel_width, pixel_height), Image.BICUBIC)
            back = backs[i * cards_width * cards_height + j].resize(
                (pixel_width, pixel_height), Image.BICUBIC).rotate(180)
            fronts_image.paste(front, (j % cards_width * pixel_width,
                                       (j // cards_width) * pixel_height))
            backs_image.paste(back, (j % cards_width * pixel_width,
                                     (j // cards_width) * pixel_height))

        fronts_image.save(f"f-{i}.jpg")
        backs_image.save(f"b-{i}.jpg")
        t_1 = threading.Thread(
            target=image_upload, args=(f"f-{i}.jpg", links)
        )
        t_1.start()
        t_2 = threading.Thread(
            target=image_upload, args=(f"b-{i}.jpg", links)
        )
        t_2.start()
        t_1.join()
        t_2.join()

def write_deck(deck_json, args, saved_objects_folder, links, num):
    """Craft the JSON for your final TTS deck Saved Object"""
    name = args.name + str(num)
    deck_json = deck_json.replace("DeckName", name)
    deck_json = deck_json.replace("FrontImageURL", links[f"f-{num}.jpg"])
    deck_json = deck_json.replace("BackImageURL", links[f"b-{num}.jpg"])
    deck_json = deck_json.replace("ReplaceGUID", f"{name}C")
    deck_json = deck_json.replace("ReplaceGUID2", f"{name}D")
    with open(saved_objects_folder + name + ".json", "w") as deck:
        deck.write(deck_json)
    copyfile("warmahordes.png", saved_objects_folder + name + ".png")

def parse_arguments():
    """Command line arg parse"""
    parser = argparse.ArgumentParser(
        description="Convert Privateer Press card pdfs to Tabletop Simulator saved deck objects."
    )
    parser.add_argument(
        "-name",
        type=str,
        help="your deck name - possibly the faction you are converting",
    )
    return parser.parse_args()

def convert():
    """This converts a cardbundle.pdf (downloaded from Privateer Press) into
    Tabletop Simulator deck Saved Objects."""
    args = parse_arguments()
    width, height, saved_objects_folder = load_config()
    if args.name is None:
        args.name = "Warmachine"
    print("Naming decks: " + args.name + "X")

    # Strip out the card images from the Privateer Press pdfs.
    card_fronts = []
    card_backs = []
    infile = "cardbundle.pdf"
    pages = convert_from_path(infile, 200, output_folder="pdf_parts")
    for page in pages:
        parse_images(card_fronts, card_backs, page)
    print("Parsing cardbundle.pdf complete.")

    # But we don't want the blank white cards.
    # I'd rather do a .filter, but I'm concerned a stray pixel would put them outta sync.
    filtered_fronts = []
    filtered_backs = []
    for i, card in enumerate(card_fronts):
        if PIL.ImageOps.invert(card).getbbox():
            filtered_fronts.append(card)
            filtered_backs.append(card_backs[i])
    print("Stripping out blank cards complete.")

    # Collate the cards into the image format Tabletop Simulator requires.
    links = {}
    deck_count = len(card_fronts) // (width*height) + 1
    package_pages(width, height, filtered_fronts, filtered_backs, deck_count, links)
    print("Packaging cards into TTS deck template images and uploading to Cloudinary complete.")

    # And let's shove em all in your Saved Objects folder :)
    deck_json = ""
    with open("decktemplate.json", "r") as deck_template:
        deck_json = deck_template.read()
    for i in range(deck_count):
        write_deck(deck_json, args, saved_objects_folder, links, i)
    print("Writing deck jsons into Saved Object folder complete.")


if __name__ == "__main__":
    convert()
