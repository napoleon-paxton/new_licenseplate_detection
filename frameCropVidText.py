import cv2
import boto3
import json

with open('credentials.json') as f:
        credentials = json.load(f)

def frameCrop(bucket, objectName, tstamp):
    print("Cropping frames from video, please wait..")
    s3_client = boto3.client('s3', 'us-east-1', aws_access_key_id=credentials["aws_access_key_id"], aws_secret_access_key=credentials['aws_secret_access_key'])
    url = s3_client.generate_presigned_url('get_object', Params = {'Bucket': bucket, 'Key': objectName}, ExpiresIn = 600)
    folder = './VideoTextDetection'
    
    cap = cv2.VideoCapture(url)

    tsFrame = tstamp

    cap.set(cv2.CAP_PROP_POS_MSEC, tsFrame)
    success, image = cap.read()
    if success:
        cv2.imwrite(folder+'/frame'+str(tstamp)+'.jpg', image)
    print("Done creating frames...")
    return 'Success'