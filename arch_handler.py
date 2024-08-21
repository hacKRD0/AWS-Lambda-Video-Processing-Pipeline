#__copyright__   = "Copyright 2024, VISA Lab"
#__license__     = "MIT"
import os
import subprocess
import boto3
import shutil
import math
# from video_splitting_cmdline import video_splitting_cmdline

AWS_ACCESS_KEY_ID=""
AWS_SECRET_ACCESS_KEY=""
REGION="us-east-1"
ASU_ID="1229524662"

s3 = boto3.client('s3', region_name=REGION, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

def video_splitting_cmdline(video_filename):
    filename = os.path.basename(video_filename)
    outdir = os.path.splitext(filename)[0]
    outdir = os.path.join("/tmp", outdir)
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    print(outdir)

    split_cmd = '/usr/bin/ffmpeg -ss 0 -r 1 -i ' +video_filename+ ' -vf fps=1/10 -start_number 0 -vframes 10 ' + outdir + "/" + 'output-%02d.jpg -y'
    try:
        subprocess.check_call(split_cmd, shell=True)
        print("Split command executed")
    except subprocess.CalledProcessError as e:
        print(e.returncode)
        print(e.output)

    fps_cmd = 'ffmpeg -i ' + video_filename + ' 2>&1 | sed -n "s/.*, \\(.*\\) fp.*/\\1/p"'
    fps = subprocess.check_output(fps_cmd, shell=True).decode("utf-8").rstrip("\n")
    fps = math.ceil(float(fps))
    return outdir

def handler(event, context):	
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
		process = subprocess.run(['python3', 'video-splitting-cmdline', object_key], capture_output=True, text=True)
		if process.returncode == 0:
			outputFile = process.stdout
		# outputFile = video_splitting_cmdline(download_path)
		print ("File split into dir: ", outputFile)
	except Exception as e:
		print("Error splitting file")
		print(str(e)) 
	# Upload the folder of split frames to s3
	try:
		frames_bucket = f'{ASU_ID}-stage-1'
		for root, dirs, files in os.walk(outputFile):
			for frame in files:
				if ".jpg" in frame:
					frame_path = os.path.join(root, frame)
					frame_number = os.path.splitext(frame)[0].split('-')[1]
					frame_key = f'{video_filename}/output_{frame_number}.jpg'
					s3.upload_file(frame_path, frames_bucket, frame_key)
					print ("Files uploaded from frame path, bucket and key: ", frame_path, frames_bucket, frame_key)
					# os.remove(frame_path)
					# print ("Files uploaded to : ", frames_bucket)
					# print ("Files uploaded with key: ", frame_key)
	except Exception as e:
		print("Error uploading split frames")
		print(str(e))
	# Delete the local file and output files
	try:
		os.remove(download_path)
		print("Video File deleted")
		shutil.rmtree(outputFile)
		print("Outdir deleted")
	except Exception as e:
		print("Error deleting file")
		print (str(e))