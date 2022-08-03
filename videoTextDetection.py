import boto3
import json
import sys
import time
from textvideoBBox import DrawBoundingBox
from frameCropVidText import frameCrop
from drawImageVTBBox import drawImageBBox

gjobid = str()
bboxresp = list()
ts_list = list()

with open('credentials.json') as f:
        credentials = json.load(f)

class VideoDetect:
    jobId = ''
    rek = boto3.client('rekognition', 'us-east-1', aws_access_key_id=credentials["aws_access_key_id"], aws_secret_access_key=credentials['aws_secret_access_key'])
    sqs = boto3.client('sqs', 'us-east-1', aws_access_key_id=credentials["aws_access_key_id"], aws_secret_access_key=credentials['aws_secret_access_key'])
    sns = boto3.client('sns', 'us-east-1', aws_access_key_id=credentials["aws_access_key_id"], aws_secret_access_key=credentials['aws_secret_access_key'])
    
    roleArn = ''
    bucket = ''
    video = ''
    startJobId = ''

    sqsQueueUrl = ''
    snsTopicArn = ''
    processType = ''

    def __init__(self, role, bucket, video):    
        self.roleArn = role
        self.bucket = bucket
        self.video = video

    def GetSQSMessageSuccess(self):

        jobFound = False
        succeeded = False
    
        dotLine=0
        while jobFound == False:
            sqsResponse = self.sqs.receive_message(QueueUrl=self.sqsQueueUrl, MessageAttributeNames=['ALL'],
                                          MaxNumberOfMessages=10)

            if sqsResponse:
                
                if 'Messages' not in sqsResponse:
                    if dotLine<40:
                        print('.', end='')
                        dotLine=dotLine+1
                    else:
                        print()
                        dotLine=0    
                    sys.stdout.flush()
                    time.sleep(5)
                    continue

                for message in sqsResponse['Messages']:
                    notification = json.loads(message['Body'])
                    rekMessage = json.loads(notification['Message'])
                    print(rekMessage['JobId'])
                    print(rekMessage['Status'])
                    if rekMessage['JobId'] == self.startJobId:
                        print('Matching Job Found:' + rekMessage['JobId'])
                        jobFound = True
                        if (rekMessage['Status']=='SUCCEEDED'):
                            succeeded=True

                        self.sqs.delete_message(QueueUrl=self.sqsQueueUrl,
                                       ReceiptHandle=message['ReceiptHandle'])
                    else:
                        print("Job didn't match:" +
                              str(rekMessage['JobId']) + ' : ' + self.startJobId)
                    # Delete the unknown message. Consider sending to dead letter queue
                    self.sqs.delete_message(QueueUrl=self.sqsQueueUrl,
                                   ReceiptHandle=message['ReceiptHandle'])


        return succeeded

    def StartTextDetection(self):
        response=self.rek.start_text_detection(Video={'S3Object': {'Bucket': self.bucket, 'Name': self.video}},
            NotificationChannel={'RoleArn': self.roleArn, 'SNSTopicArn': self.snsTopicArn})

        self.startJobId=response['JobId']
        print('Start Job Id: ' + self.startJobId)
  
    def GetTextDetectionResults(self):
        maxResults = 10000
        paginationToken = ''
        finished = False
        global gjobid
        global bboxresp
        gjobid = self.startJobId
        
        while finished == False:
            response = self.rek.get_text_detection(JobId=self.startJobId,
                                            MaxResults=maxResults,
                                            NextToken=paginationToken)
            bboxresp.append(response)

            for textDetection in response['TextDetections']:
                text=textDetection['TextDetection']

                print("Timestamp: " + str(textDetection['Timestamp']))
                print("   Text Detected: " + text['DetectedText'])
                print("   Confidence: " +  str(text['Confidence']))
                print ("      Bounding box")
                print ("        Top: " + str(text['Geometry']['BoundingBox']['Top']))
                print ("        Left: " + str(text['Geometry']['BoundingBox']['Left']))
                print ("        Width: " +  str(text['Geometry']['BoundingBox']['Width']))
                print ("        Height: " +  str(text['Geometry']['BoundingBox']['Height']))
                print ("   Type: " + str(text['Type']) )
                print()
                #bboxresp.append(textDetection)

            if 'NextToken' in response:
                paginationToken = response['NextToken']
            else:
                finished = True
        return response
        
    def CreateTopicandQueue(self):
      
        millis = str(int(round(time.time() * 1000)))

        #Create SNS topic
        
        snsTopicName="AmazonRekognitionExample" + millis

        topicResponse=self.sns.create_topic(Name=snsTopicName)
        self.snsTopicArn = topicResponse['TopicArn']

        #create SQS queue
        sqsQueueName="AmazonRekognitionQueue" + millis
        self.sqs.create_queue(QueueName=sqsQueueName)
        self.sqsQueueUrl = self.sqs.get_queue_url(QueueName=sqsQueueName)['QueueUrl']
 
        attribs = self.sqs.get_queue_attributes(QueueUrl=self.sqsQueueUrl,
                                                    AttributeNames=['QueueArn'])['Attributes']
                                        
        sqsQueueArn = attribs['QueueArn']

        # Subscribe SQS queue to SNS topic
        self.sns.subscribe(
            TopicArn=self.snsTopicArn,
            Protocol='sqs',
            Endpoint=sqsQueueArn)

        #Authorize SNS to write SQS queue 
        policy = """{{
  "Version":"2012-10-17",
  "Statement":[
    {{
      "Sid":"MyPolicy",
      "Effect":"Allow",
      "Principal" : {{"AWS" : "*"}},
      "Action":"SQS:SendMessage",
      "Resource": "{}",
      "Condition":{{
        "ArnEquals":{{
          "aws:SourceArn": "{}"
        }}
      }}
    }}
  ]
}}""".format(sqsQueueArn, self.snsTopicArn)
 
        response = self.sqs.set_queue_attributes(
            QueueUrl = self.sqsQueueUrl,
            Attributes = {
                'Policy' : policy
            })

    def DeleteTopicandQueue(self):
        self.sqs.delete_queue(QueueUrl=self.sqsQueueUrl)
        self.sns.delete_topic(TopicArn=self.snsTopicArn)


def TextDetection(video):
    roleArn = 'arn:aws:iam::449917476606:role/labrekog118-example-video-rekognition'   
    bucket = 'rohitchalicerekog'
    #video = 'accident_scene.mp4'
    bbrespFull = list()

    analyzer=VideoDetect(roleArn, bucket,video)
    analyzer.CreateTopicandQueue()

    analyzer.StartTextDetection()
    if analyzer.GetSQSMessageSuccess()==True:
        analyzer.GetTextDetectionResults()
    
    for i in range(len(bboxresp)):
        bbrespFull.extend(bboxresp[i]['TextDetections'])
    
    DrawBoundingBox(bucket, video, bbrespFull)

    #Collect timestamps so you can crop those frames
    for x in bbrespFull:
        if (x['TextDetection']['DetectedText'].isupper() and len(x['TextDetection']['DetectedText']) > 5 and len(x['TextDetection']['DetectedText']) < 9 and x['TextDetection']['Type'] == 'WORD'):
            ts_list.append(x['Timestamp'])
        else:
            continue

    #For cropping the frames and drawing image boundary boxes
    for ts in ts_list:
        frameCrop(bucket, video, ts)
        for box in bbrespFull:
            if (box['TextDetection']['DetectedText'].isupper() and len(box['TextDetection']['DetectedText']) > 5 
            and len(box['TextDetection']['DetectedText']) < 9 and box['TextDetection']['Type'] == 'WORD' and box['Timestamp'] == ts):
                bbox = box['TextDetection']
                fName = 'frame'+str(ts)+'.jpg'
                print("FileName is: ",fName)
                drawImageBBox(fName, ts, bbox)
    
    print("Completed drawing of all bounding boxes..")

    with open ('videoTextDetection.json', 'w') as outfile:
        json.dump(bboxresp, outfile)
    
    clist = list()
    for i in bbrespFull:
        for j in i['TextDetections']:
            if (j['TextDetection']['Type'] == 'WORD' and j['TextDetection']['Confidence'] > 95 and len(j['TextDetection']['DetectedText']) > 5 and len(j['TextDetection']['DetectedText']) < 9):
                clist.append(j['TextDetection']['DetectedText'])
    
    occurrence = {item: clist.count(item) for item in clist}

    with open("licenseplate_summary.txt", "w") as f:
        for k,v in occurrence.items():
            f.write(str(v) + " " + str(k) + "\n")

    analyzer.DeleteTopicandQueue()
    return bbrespFull

# if __name__ == "__main__":
#     main()