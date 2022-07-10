import cv2
import boto3
import json

# f = open('resp_json_data.json')

# boxes = json.load(f)

with open('credentials.json') as f:
        credentials = json.load(f)

def DrawBoundingBox(bucket, objectName, boxes):
    print("Creating video with bounding boxes for captured text, please wait..")
    s3_client = boto3.client('s3', 'us-east-1', aws_access_key_id=credentials["aws_access_key_id"], aws_secret_access_key=credentials['aws_secret_access_key'])
    url = s3_client.generate_presigned_url('get_object', 
                                       Params = {'Bucket': bucket, 'Key': objectName}, 
                                       ExpiresIn = 600)
    cap = cv2.VideoCapture(url)
    fps = cap.get(cv2.CAP_PROP_FPS)
    img_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    img_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
    video = cv2.VideoWriter('./output.mp4', fourcc, fps, (img_width, img_height))

    cur_idx = 0
    left = int(boxes[cur_idx]['TextDetection']['Geometry']['BoundingBox']['Left'] * img_width)
    top = int(boxes[cur_idx]['TextDetection']['Geometry']['BoundingBox']['Top'] * img_height)
    right = int((boxes[cur_idx]['TextDetection']['Geometry']['BoundingBox']['Left'] + boxes[cur_idx]['TextDetection']['Geometry']['BoundingBox']['Width']) * img_width)
    bottom = int((boxes[cur_idx]['TextDetection']['Geometry']['BoundingBox']['Top'] + boxes[cur_idx]['TextDetection']['Geometry']['BoundingBox']['Height']) * img_height)

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        Timestamp = cap.get(cv2.CAP_PROP_POS_MSEC)
        if cur_idx < len(boxes) - 1 and Timestamp >= boxes[cur_idx + 1]['Timestamp']:
            cur_idx += 1
            left = int(boxes[cur_idx]['TextDetection']['Geometry']['BoundingBox']['Left'] * img_width)
            top = int(boxes[cur_idx]['TextDetection']['Geometry']['BoundingBox']['Top'] * img_height)
            right = int((boxes[cur_idx]['TextDetection']['Geometry']['BoundingBox']['Left'] + boxes[cur_idx]['TextDetection']['Geometry']['BoundingBox']['Width']) * img_width)
            bottom = int((boxes[cur_idx]['TextDetection']['Geometry']['BoundingBox']['Top'] + boxes[cur_idx]['TextDetection']['Geometry']['BoundingBox']['Height']) * img_height)

        cv2.rectangle(frame, (left, top), (right, bottom), (255, 255, 0))
        cv2.putText(frame, boxes[cur_idx]['TextDetection']['DetectedText'], (left, top), cv2.FONT_HERSHEY_SIMPLEX, 1, color=(0,255,0))
        video.write(frame)
    
    cap.release()
    video.release()

# if __name__ == "__main__":
#     DrawBoundingBox('rohitchalicerekog', 'bezos_vogel.mp4')