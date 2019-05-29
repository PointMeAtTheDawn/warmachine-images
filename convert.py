from PIL import Image
from pdf2image import convert_from_path

def crop(image_path, coords, saved_location):
    """
    @param image_path: The path to the image to edit
    @param coords: A tuple of x/y coordinates (x1, y1, x2, y2)
    @param saved_location: Path to save the cropped image
    """
    image_obj = Image.open(image_path)
    cropped_image = image_obj.crop(coords)
    cropped_image.save(saved_location)
 
if __name__ == '__main__':
    infile = 'cardbundle.pdf'
    pages = convert_from_path(infile)
    cardFronts = []
    cardBacks = []
    for page in pages:
        cardFronts.append(page.crop((94,151,592,852)))
        cardFronts.append(page.crop((597,151,1095,852)))
        cardFronts.append(page.crop((1099,151,1598,852)))
        cardFronts.append(page.crop((1602,151,2101,852)))
        cardBacks.append(page.crop((94,855,592,1553)))
        cardBacks.append(page.crop((597,855,1095,1553)))
        cardBacks.append(page.crop((1099,855,1598,1553)))
        cardBacks.append(page.crop((1602,855,2101,1553)))
    
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