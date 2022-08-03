# License Plate Detection

We have used Amazon Rekognition API for License plates and for reading text in video files.

The solution can detect license plates from a stored video or a live stream, and the model's accuracy is 90% and above. Not only can we read license plates, but also signboards and any text within the video frame.
<img width="1482" alt="image" src="https://user-images.githubusercontent.com/76990450/182540815-d0a8a003-a8d2-4cd3-9aee-84958eba16e3.png">



Once we upload the video to the S3 bucket, the same lambda function which is used by all our other components, invokes this Rekognition API and kicks of a job. 
Depending on the size of the file, the job takes time to read frame by frame. Once the job successfully completes, we kick off another API that gets information of the text identified, along with the bounding boxes, timestamp and so on.

We have utilized SNS topic and SQS queuing messaging services to communicate and track status of the job.

Finally, the python script takes that information and writes the images and video output, but now with both text and bounding boxes superimposed on the files. They all land to the S3 bucket.
