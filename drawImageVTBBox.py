from PIL import Image, ImageDraw
import io
import json
import boto3
from datetime import datetime
import unicodedata
from PIL import Image, ImageDraw, ImageFont

with open('credentials.json') as f:
        credentials = json.load(f)

s3_client = boto3.client('s3', aws_access_key_id=credentials["aws_access_key_id"], aws_secret_access_key=credentials['aws_secret_access_key'])
date = datetime.now().strftime("%Y_%m_%d-%I:%M:%S_%p")

def drawImageBBox(frameName, tstamp, boxes):
    print("Drawing bounding box for each frame captured, please wait..")
    folder = './VideoTextDetection/'
    mem_file = io.BytesIO()
    dText = boxes['DetectedText']
    stripText = unicodedata.normalize('NFD', dText).encode('ascii', 'ignore').decode("utf-8")
    
    image=Image.open(folder+frameName)
    imgWidth, imgHeight = image.size  
    draw = ImageDraw.Draw(image)
    font=ImageFont.truetype("arial.ttf",size=20)

    box = boxes['Geometry']['BoundingBox']
    left = imgWidth * box['Left']
    top = imgHeight * box['Top']
    width = imgWidth * box['Width']
    height = imgHeight * box['Height']

    # print('Left: ' + '{0:.0f}'.format(left))
    # print('Top: ' + '{0:.0f}'.format(top))
    # print('Face Width: ' + "{0:.0f}".format(width))
    # print('Face Height: ' + "{0:.0f}".format(height))

    points = (
        (left,top),
        (left + width, top),
        (left + width, top + height),
        (left , top + height),
        (left, top)

    )
    draw.line(points, fill='#00d400', width=3)
    draw.text((left, top+height), stripText, font=font, fill='red')
    image.save(folder+'frame'+str(tstamp)+'.jpg')
    image.save(mem_file, format=image.format)
    mem_file.seek(0)
    s3_client.upload_fileobj(mem_file, 'rohitchalicerekog', 'Output/TextDetectedVideo_'+str(date)+'.jpg')

        # Alternatively can draw rectangle. However you can't set line width.
        #draw.rectangle([left,top, left + width, top + height], outline='#00d400') 
    #image.show()
