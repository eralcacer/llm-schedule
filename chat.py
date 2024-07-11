import datetime, os
from llm_schedule.llm_final import MeetingScheduler

from google_drive.google_drive import DriveAPI
from dotenv import load_dotenv

load_dotenv()

FILE_ID = os.getenv("FILE_ID")
FILE_NAME = os.getenv("FILE_NAME")

class Chat:
    def __init__(self):
        self.drive_api = DriveAPI()
        self.scheduler = MeetingScheduler()
        self.chat_active = True

    def parse_response(self, response):
        # Parse the response to extract the meeting details
        can_schedule = response.split(" ")[0]

        return can_schedule == "True"
    
    def download_and_load_content(self):
        self.drive_api.download_content_file(FILE_ID, FILE_NAME)
        self.scheduler.set_txt_loader()

    def parse_date(self, format_date_input):
        # Parse the user input for the date
        try:
            year, month, day, hour, minutes = map(int, format_date_input.split(","))
            return datetime.datetime(year, month, day, hour, minutes)
        except ValueError:
            print("Invalid date format. Please enter the date as 'day month year'.")
            return None


    def start_chat(self):
        while self.chat_active is True:
            try:
                query = input('Schedule a meeting with Enrique: ')

                if query.strip().lower() == "exit" or query.strip().lower() == "bye":
                    self.chat_active = False
                else:
                    response_query, response_is_meting_scheduled = self.scheduler.submit_new_query(query)
                    
                    print(response_query + "\n")

                    parsed_date = None
                    meeting_subject = None
                    email = None
                    if self.parse_response(response_is_meting_scheduled) == True:
                        while True:
                            try:
                                format_date_input = input("Specify the date and time for your meeting as yyyy, mm, dd, 24, mm: ")
                                if format_date_input.lower() == "cancel" or format_date_input.lower() == "exit":
                                    break
                                parsed_date = self.parse_date(format_date_input)
                                if parsed_date:
                                    meeting_subject = input("Specify a title for the meeting: ")
                                if meeting_subject:
                                    email = input("What is the best email for a reminder?")
                                if email:
                                    break
                            except: 
                                print("error")
                        
                        if parsed_date:
                            # If event created successfully insert the meeting date to the google doc and update the local file
                            end_datetime = parsed_date + datetime.timedelta(hours=1) 
                            text_insert = "-"  + parsed_date.strftime('%A') + " at " + parsed_date.strftime("%I:%M %p") + " to " + end_datetime.strftime("%I:%M %p") + " " + meeting_subject + ". Date: " + parsed_date.strftime('%Y-%m-%d')
                            insert_event_doc = self.drive_api.insert_text_doc(text_insert)
                            event_creation = self.drive_api.add_event(parsed_date, meeting_subject, email)
                            self.download_and_load_content()

            except KeyboardInterrupt:
                print("Bye!")
                break



if __name__ == "__main__":
    chat = Chat()
    chat.start_chat()