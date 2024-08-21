1. Author lambda funtion from scratch
2. Configs: 512 memory, 1024 ephereal memory, 15min function timeout
3. Deploy https://serverlessrepo.aws.amazon.com/applications/
4. Edits to be made in layer config json

```json
us-east-1/145266761615/ffmpeg-lambda-layer
{
    "Version": "2012-10-17",
    "Statement": [
            {
            "Effect": "Allow",
            "Action": "lambda:InvokeFunction",
            "Resource": "arn:aws:lambda:us-east-1:381492163993:function:face-recognition"
            }
    ]
}
```
