import boto3
import os
import cv2
import json
from PIL import Image, ImageDraw, ImageFont
from facenet_pytorch import MTCNN, InceptionResnetV1
from shutil import rmtree
import numpy as np
import torch

os.environ["TORCH_HOME"] = "/tmp/torch"

AWS_ACCESS_KEY_ID=""
AWS_SECRET_ACCESS_KEY=""
REGION="us-east-1"
ASU_ID="1229524662"

s3 = boto3.client('s3', region_name=REGION, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
lambda_client = boto3.client('lambda', region_name=REGION, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

mtcnn = MTCNN(image_size=240, margin=0, min_face_size=20) # initializing mtcnn for face detection
resnet = InceptionResnetV1(pretrained='vggface2').eval() # initializing resnet for face img to embeding conversion

def face_recognition_function(key_path):
    # Face extraction
	img = cv2.imread(key_path, cv2.IMREAD_COLOR)
	boxes, _ = mtcnn.detect(img)

    # Face recognition
	key = os.path.splitext(os.path.basename(key_path))[0].split(".")[0]
	img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
	face, prob = mtcnn(img, return_prob=True, save_path=None)
	saved_data = torch.load('/tmp/data.pt')  # loading data.pt file
	if face != None:
		emb = resnet(face.unsqueeze(0)).detach()  # detech is to make required gradient false
		embedding_list = saved_data[0]  # getting embedding data
		name_list = saved_data[1]  # getting list of names
		dist_list = []  # list of matched distances, minimum distance is used to identify the person
		for idx, emb_db in enumerate(embedding_list):
			dist = torch.dist(emb, emb_db).item()
			dist_list.append(dist)
		idx_min = dist_list.index(min(dist_list))

		# Save the result name in a file
		with open("/tmp/" + key + ".txt", 'w+') as f:
			f.write(name_list[idx_min])
		return "/tmp/" + key + ".txt", name_list[idx_min]
	else:
		print(f"No face is detected")
	return ""

def handler(event, context):	
	bucket_name = f'{ASU_ID}-stage-1'
	datapt_bucket = f'{ASU_ID}-temp'
	object_key = event['image']
	datapt_key = 'data.pt'
	download_path = f'/tmp/{object_key}'
	datapt_path = f'/tmp/data.pt'
	# Store the image file locally
	print("Download path = ", download_path)
	try:
		s3.download_file(bucket_name, object_key, download_path)
		print ("Image downloaded at: ", download_path)
		s3.download_file(datapt_bucket, datapt_key,datapt_path)
		print ("data.pt downloaded")
	except Exception as e:
		print("Error downloading file")
		print(str(e))

	# Execute the face-recognition python program
	try:
		outputPath, output = face_recognition_function(download_path)
		print ("Face recognition result: ", output)
		print ("Output file at:", outputPath)
	except Exception as e:
		print("Error recognizing face")
		print(str(e)) 

	# Upload the output to s3
	try:
		output_bucket = f'{ASU_ID}-output'
		output_key = outputPath.split("/")[-1]
		s3.upload_file(outputPath, output_bucket, output_key)
		print ("File uploaded from frame path ", outputPath, "to bucket", output_bucket, "with key as ", output_key)
	except Exception as e:
		print("Error uploading output file")
		print(str(e))

	# Delete the local file and output files
	try:
		os.remove(download_path)
		print("Image File deleted")
		os.remove(outputPath)
		print("outputPath deleted")
	except Exception as e:
		print("Error deleting files")
		print (str(e))