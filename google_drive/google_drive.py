import io
import pickle 
import os.path 
import shutil
import datetime

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

from dotenv import load_dotenv

load_dotenv()

SCOPES = [os.getenv("GOOGLE_DRIVE_SCOPE1"), os.getenv("GOOGLE_DRIVE_SCOPE2"), os.getenv("GOOGLE_DRIVE_SCOPE3")]
FILE_ID = os.getenv("FILE_ID")
FILE_NAME = os.getenv("FILE_NAME")

class DriveAPI:

    def __init__(self):
        self.creds = self.get_credentials()
        self.service = build('drive', 'v3', credentials=self.creds)
        self.calendar_service = build('calendar', 'v3', credentials=self.creds)
        self.docs_service = build('docs', 'v1', credentials=self.creds)

    def get_credentials(self):
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                return pickle.load(token)

        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
        return creds

    def download_file(self, real_file_id, file_name):
        try:
            file = self.service.files().get(fileId=real_file_id).execute()
            mime_type = file['mimeType']

            if 'application/vnd.google-apps' in mime_type:
                request = self.service.files().export(fileId=real_file_id, mimeType='text/plain')
                file_name += ".txt"
            else:
                request = self.service.files().get_media(fileId=real_file_id)

            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request, chunksize=204800)
            done = False

            while not done:
                status, done = downloader.next_chunk()

            fh.seek(0)
            with open(file_name, 'wb') as f:
                shutil.copyfileobj(fh, f)

            print("File Downloaded")
            return True
        except HttpError as e:
            print(f"HTTP error occurred: {e}")
            return False
        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    def download_content_file(self, real_file_id, file_name):
        try:
            file = self.service.files().export(fileId=real_file_id, mimeType='text/plain').execute()
            content = file.decode('utf-8')
            with open('content.txt', 'w', encoding='utf-8') as f:
                f.write(content)

            print("Content written to content.txt successfully.")
            return True
        except HttpError as e:
            print(f"HTTP error occurred: {e}")
            return False
        except Exception as e:
            print(f"An error occurred: {e}")
            return False
    
    def insert_text_doc(self, text):
        insert_text = text + "\n"
        requests = [
            {
                'insertText': {
                    'endOfSegmentLocation': {},
                    'text': insert_text
                }
            },
        ]

        result = self.docs_service.documents().batchUpdate(documentId=FILE_ID, body={'requests': requests}).execute()
        


    def get_calendar_events(self):
        try:
            now = datetime.datetime.utcnow().isoformat() + "Z"
            events_result = self.calendar_service.events().list(calendarId='primary', timeMin=now,
                                                                maxResults=100, singleEvents=True,
                                                                orderBy='startTime').execute()
            # print(events_result)
            events = events_result.get('items', [])

            if not events:
                print('No upcoming events found.')
                return None
            else:
                print('Upcoming events:')
                for event in events:
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    # print(start, event['summary'])
                return events
        except HttpError as e:
            print(f"HTTP error occurred: {e}")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def add_event(self, parsed_date, meeting_subject, requestor_email):
        end_datetime = parsed_date + datetime.timedelta(hours=1) 
        event = {
                'summary': meeting_subject,
                'location': 'Zoom',
                'description': '',
                'start': {
                    'dateTime': parsed_date.strftime('%Y-%m-%dT%H:%M:%S'),
                    'timeZone': 'America/Los_Angeles',
                },
                'end': {
                    'dateTime': end_datetime.strftime('%Y-%m-%dT%H:%M:%S'),
                    'timeZone': 'America/Los_Angeles',
                },
                'attendees': [
                    {'email': 'enrique.alcacer@gmail.com'},
                    {'email': requestor_email},
                ],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 10},
                    ],
                },
            }

        event = self.calendar_service.events().insert(calendarId='primary', body=event).execute()
        print('Event created: %s' % (event.get('htmlLink')))
        return event
    


if __name__ == "__main__":
    obj = DriveAPI()
    real_file_id = FILE_ID
    file_name = FILE_NAME
    obj.get_calendar_events()
    obj.download_content_file(real_file_id, file_name)
