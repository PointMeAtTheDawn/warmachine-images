import requests
import argparse
import os
import threading
from PIL import Image
from pdf2image import convert_from_path
from base64 import b64encode

def parse_images(fronts, backs, page):
    fronts.append(page.crop((94,151,592,852)))
    fronts.append(page.crop((597,151,1095,852)))
    fronts.append(page.crop((1099,151,1598,852)))
    fronts.append(page.crop((1602,151,2101,852)))
    backs.append(page.crop((94,855,592,1553)))
    backs.append(page.crop((597,855,1095,1553)))
    backs.append(page.crop((1099,855,1598,1553)))
    backs.append(page.crop((1602,855,2101,1553)))

def imgur_upload(args, links, image, name):
    image.save(name)
        
    headers = {"Authorization": f'Client-ID {args.imgurClientID}'}
    r = requests.post(
        'https://api.imgur.com/3/upload.json',
        headers = headers,
        data = {
            'key': args.imgurAPIKey,
            'image': b64encode(open(name, 'rb').read()),
            'type': 'base64',
            'name': name,
            'title': name
        }
    )
    print(r.json())
    links[name] = r.json()["data"]["link"]
    os.remove(name)

def package_page(args, links, cardFronts, cardBacks):
    fronts = Image.new('RGB',(2988,3505))
    backs = Image.new('RGB',(2988,3505))
    for j in range(30):
        if len(cardFronts) <= i*30+j:
            continue
        fronts.paste(cardFronts[i*30+j], (j%6*498,(j//6)*701))
        backs.paste(cardBacks[i*30+j].rotate(180), (j%6*498,(j//6)*701))
    t1 = threading.Thread(target=imgur_upload, args=(args,links,fronts,f'f-{i}.png'))
    t1.start()
    t2 = threading.Thread(target=imgur_upload, args=(args,links,backs,f'b-{i}.png'))
    t2.start()
    t1.join()
    t2.join()

def write_deck(deckJSON, args, links, num):
    name = args.faction + str(num)
    deckJSON = deckJSON.replace("DeckName", name)
    deckJSON = deckJSON.replace("FrontImageURL", links[f'f-{i}.png'])
    deckJSON = deckJSON.replace("BackImageUrl", links[f'b-{i}.png'])
    deckJSON = deckJSON.replace("ReplaceGUID", f'{name}C')
    deckJSON = deckJSON.replace("ReplaceGUID2", f'{name}D')
    with open(args.savedObjectsFolder+name+".json", 'w') as deck:
        deck.write(deckJSON)
 
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Convert Privateer Press card pdfs to Tabletop Simulator saved deck objects.')
    parser.add_argument('faction', type=str, help='name of the faction you are converting to decks.')
    parser.add_argument('imgurClientID', type=str, help='clientID in imgur.')
    parser.add_argument('imgurAPIKey', type=str, help='API key in imgur.')
    parser.add_argument('savedObjectsFolder', type=str, help='Your Saved Objects folder, include two trailing slashes cuz I am lazy.')
    args = parser.parse_args()

    # Strip out the card images from the Privateer Press pdfs.
    cardFronts = []
    cardBacks = []
    infile = 'cardbundle.pdf'
    pages = convert_from_path(infile)
    for page in pages:
        parse_images(cardFronts, cardBacks, page)
    
    # Collate the cards into the image format Tabletop Simulator requires.
    links = {}
    deckCount = len(cardFronts)//30+1

    for i in range(deckCount):
        package_page(args, links, cardFronts, cardBacks)
    
    # Wait for all of the imgur uploads to finish - nvm, this causes a MemoryError I'm too lazy to track down :p.
    # for thread in threads:
    #     thread.join()

    deckJSON = ''
    with open('decktemplate.json', 'r') as deckTemplate:
        deckJSON = deckTemplate.read()
    
    for i in range(deckCount):
        write_deck(deckJSON, args, links, i)