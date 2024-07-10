from llm_schedule.llm_final import MeetingScheduler

class Chat:
    def __init__(self):
        self.scheduler = MeetingScheduler()
        self.chat_active = True

    def start_chat(self):
        while self.chat_active is True:
            query = input('Schedule a meeting with Enrique: ')

            if query.strip().lower() == "exit" or query.strip().lower() == "bye":
                self.chat_active = False
            else:
                response_query, response_is_meting_scheduled = self.scheduler.submit_new_query(query)

                print(response_query + "\n")

if __name__ == "__main__":
    chat = Chat()
    chat.start_chat()