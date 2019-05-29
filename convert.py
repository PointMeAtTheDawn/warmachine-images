from PIL import Image
from pdf2image import convert_from_path

def parse_images(fronts, backs, page):
    fronts.append(page.crop((94,151,592,852)))
    fronts.append(page.crop((597,151,1095,852)))
    fronts.append(page.crop((1099,151,1598,852)))
    fronts.append(page.crop((1602,151,2101,852)))
    backs.append(page.crop((94,855,592,1553)))
    backs.append(page.crop((597,855,1095,1553)))
    backs.append(page.crop((1099,855,1598,1553)))
    backs.append(page.crop((1602,855,2101,1553)))
 
if __name__ == '__main__':
    infile = 'cardbundle.pdf'
    pages = convert_from_path(infile)
    cardFronts = []
    cardBacks = []
    for page in pages:
        parse_images(cardFronts, cardBacks, page)
    
    for i in range(len(cardFronts)//40+1):
        fronts = Image.new('RGB',(3984,3505))
        backs = Image.new('RGB',(3984,3505))
        for j in range(40):
            if len(cardFronts) <= i*40+j:
                continue
            fronts.paste(cardFronts[i*40+j], (j%8*498,(j//8)*701))
            backs.paste(cardBacks[i*40+j].rotate(180), (j%8*498,(j//8)*701))

        fronts.save(f'fronts{i}.png')
        backs.save(f'backs{i}.png')