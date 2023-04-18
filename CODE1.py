import os
import toml
import pandas as pd
from datetime import datetime, timezone
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from linkedin_api import Linkedin
import facebook


# Load configuration from TOML file
#with open('secret.toml') as f:
#   secret = toml.load(f)
#with open('C:\Users\theli\OneDrive\Desktop\PLACEMENT PRACTICE\Chatbot\Team6\secret.toml', 'r') as f:
#    secret=toml.load(f)
with open('C:\\Users\\theli\\OneDrive\\Desktop\\PLACEMENT PRACTICE\\Chatbot\\Team6\\secert.toml', 'r') as f:
    secret=toml.load(f)
openai_secret_key = secret['openai']["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"]

   
# Authenticate with YouTube API
creds = Credentials.from_authorized_user_file( secret['youtube']['credentials_path'], ['https://www.googleapis.com/auth/youtube.upload'])
youtube = build('youtube', 'v3', credentials=creds)

# Authenticate with LinkedIn API
linkedin = Linkedin(secret['linkedin']['email'], secret['linkedin']['password'])

# Authenticate with Facebook API
graph = facebook.GraphAPI(access_token=secret['facebook']['access_token'], version=secret['facebook']['version'])

# Load schedule from Excel file
#df = pd.read_excel(secret['socialauto']["C:\Users\theli\OneDrive\Desktop\PLACEMENT PRACTICE\Chatbot\Team6\socialauto.xlsx"], sheet_name=secret['socialauto']['sheet_name'])

file_path = "C:\\Users\\theli\\OneDrive\\Desktop\\PLACEMENT PRACTICE\\Chatbot\\Team6\\socialauto.xlsx"
sheet_name = "socialauto.xlsx"
# Read the Excel file into a DataFrame
df = pd.read_excel(file_path, sheet_name=sheet_name)


# Iterate over each row in the schedule
for index, row in df.iterrows():
    # Get metadata for the video/post
    title = row['Title']
    description = row['Description']
    tags = row['Tags'].split(', ')
    publish_date = datetime.strptime(row['Publish Date'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
    video_path = row['Video Path']
    image_path = row['Image Path']

    # Determine which platform to post to based on the sheet name
    platform = row['Platform'].lower()
    if platform == 'youtube':
        # Upload video to YouTube
        request_body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags
            },
            'status': {
                'privacyStatus': 'private' if publish_date > datetime.now(timezone.utc) else 'public'
            }
        }
        media_file = MediaFileUpload(video_path)
        response = youtube.videos().insert(
            part='snippet,status',
            body=request_body,
            media_body=media_file
        ).execute()
        video_id = response['id']

        # Update thumbnail image
        if image_path:
            media_file = MediaFileUpload(image_path)
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=media_file
            ).execute()

        # Publish video if publish date has passed
        if publish_date <= datetime.now(timezone.utc):
            youtube.videos().update(
                part='status',
                body={
                    'id': video_id,
                    'status': {
                        'privacyStatus': 'public'
                    }
                }
            ).execute()

    elif platform == 'linkedin':
        # Upload post to LinkedIn
        linkedin.post_share(
            text=title + '\n\n' + description,
            share_media_category='VIDEO',
            media=[
                {
                    'status': 'READY',
                    'description': title,
                    'originalUrl': video_path,
                    'title': title,
                    'media': 'VIDEO'
                }
            ]
        )

    elif platform == 'facebook':
        # Upload post to Facebook
        with open(video_path, 'rb') as video_file:
            response = graph.put_video(
                video_file,
                title=title,
                description=description,
                thumbnail=open(image_path, 'rb')
            )
           
