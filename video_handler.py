import os
import subprocess
import boto3
import shutil
import math
import json

AWS_ACCESS_KEY_ID=""
AWS_SECRET_ACCESS_KEY=""
REGION="us-east-1"
ASU_ID="1229524662"

s3 = boto3.client('s3', region_name=REGION, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
lambda_client = boto3.client('lambda', region_name=REGION, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

def video_splitting_cmdline(video_filename):
    filename = os.path.basename(video_filename)
    outfile = os.path.splitext(filename)[0] + ".jpg"

    split_cmd = 'ffmpeg -i ' + video_filename + ' -vframes 1 ' + '/tmp/' + outfile
    try:
        subprocess.check_call(split_cmd, shell=True)
    except subprocess.CalledProcessError as e:
        print(e.returncode)
        print(e.output)

    fps_cmd = 'ffmpeg -i ' + video_filename + ' 2>&1 | sed -n "s/.*, \\(.*\\) fp.*/\\1/p"'
    fps = subprocess.check_output(fps_cmd, shell=True).decode("utf-8").rstrip("\n")
    return outfile

def lambda_handler(event, context):	
	bucket_name = f'{ASU_ID}-input'
	object_key = event['Records'][0]['s3']['object']['key']	
	video_filename = os.path.splitext(object_key)[0]
	download_path = f'/tmp/{object_key}'
	print("video filename: ", video_filename, object_key)
	# Store the mp4 file locally
	print("Download path = ", download_path)
	try:
		s3.download_file(bucket_name, object_key, download_path)
		print ("File downloaded at: ", download_path)
	except Exception as e:
		print("Error downloading file")
		print(str(e))
	# Execute the video-splitting python program
	try:
		# process = subprocess.run(['python3', 'video-splitting-cmdline', object_key], capture_output=True, text=True)
		# if process.returncode == 0:
		# 	outputFile = process.stdout
		outputFile = video_splitting_cmdline(download_path)
		print ("Image upload path: ", outputFile)
	except Exception as e:
		print("Error splitting file")
		print(str(e)) 
	# Upload the folder of split frames to s3
	try:
		frame_bucket = f'{ASU_ID}-stage-1'
		frame_path = os.path.join('/tmp', outputFile)
		frame_key = f'{video_filename}.jpg'
		s3.upload_file(frame_path, frame_bucket, frame_key)
		print ("File uploaded from frame path ", frame_path, "to bucket", frame_bucket, "with key as ", frame_key)

		# for root, dirs, files in os.walk(outputFile):
		# 	for frame in files:
		# 		if ".jpg" in frame:
		# 			frame_number = os.path.splitext(frame)[0].split('-')[1]
		# 			frame_key = f'{video_filename}/output_{frame_number}.jpg'
					# s3.upload_file(frame_path, frame_bucket, frame_key)
					# print ("Files uploaded from frame path, bucket and key: ", frame_path, frame_bucket, frame_key)
					# os.remove(frame_path)
					# print ("Files uploaded to : ", frame_bucket)
					# print ("Files uploaded with key: ", frame_key)
	except Exception as e:
		print("Error uploading split frames")
		print(str(e))

	# Delete the local file and output files
	try:
		os.remove(download_path)
		print("Video File deleted")
		os.remove(frame_path)
		# shutil.rmtree(outputFile)
		print("outputFile deleted")
	except Exception as e:
		print("Error deleting files")
		print (str(e))

	try:		
		print ("invoking")
		# Trigger face-recognition Lambda function
		response = lambda_client.invoke(
			FunctionName='face-recognition',
			InvocationType='Event',
			Payload=json.dumps({"image": frame_key})
		)
		
		# Extract and process response
		response_payload = json.loads(response['Payload'].read().decode("utf-8"))
		print("Invocation successful:", response_payload)
	except Exception as e:
		print("Error invoking face-recognition function")
		print(e)
