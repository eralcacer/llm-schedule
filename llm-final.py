import openai
from openai import OpenAI
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
from langchain.chains.question_answering import load_qa_chain

from dotenv import load_dotenv
# from google_drive import DriveAPI
import os

load_dotenv()

openai.api_key = os.getenv("OPEN_API_KEY")

chat = ChatOpenAI(model="gpt-3.5-turbo-0125")

class MeetingSheduler:
    def __init__(self):
        # self.drive_api = DriveAPI()
        self.messages = ["Create an appointment with Enrique on July 7th at 2:30 PM."]

        self.loader = TextLoader("../content.txt")
        self.doc = self.loader.load()

        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=0)
        self.all_splits = self.text_splitter.split_documents(self.doc)
        
        self.vectorstore = Chroma.from_documents(documents=self.all_splits, embedding=OpenAIEmbeddings())

        self.retriever = self.vectorstore.as_retriever()
        
        self.chain = load_qa_chain(chat, chain_type="stuff", verbose=True)

        self.retriever = self.vectorstore.as_retriever(k=4)

        self.docs = self.retriever.invoke("Can LangSmith help test my LLM applications?")

        # self.contextualize_q_system_prompt = """Given a chat history and the latest user question \
        # which might reference context in the chat history, formulate a standalone question \
        # which can be understood without the chat history. Do NOT answer the question, \
        # just reformulate it if needed and otherwise return it as is."""
        
        # self.contextualize_q_prompt = ChatPromptTemplate.from_messages(
        #     [
        #         ("system", self.contextualize_q_system_prompt),
        #         MessagesPlaceholder("messages"),
        #     ]
        # )

        # self.history_aware_retriever = create_history_aware_retriever(llm, self.retriever, self.contextualize_q_prompt)

        self.template_rag = """
        Answer the user's questions based on the below context.
        Based on the document's information, you need to find if a user that chats with you can schedule a meeting with Enrique Alcacer. 
        Assume that if the context doesn't contain information about a specified time and day in the question, Enrique is available.
        If according to the context, the specified time by the question Enrique not is available, give suggestions when Enrique is free based on the context.
        If you don't know the answer, just say that you don't know:
        <context>
        {context}
        <context>
        """

        self.question_answering_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    self.template_rag,
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        self.document_chain = create_stuff_documents_chain(chat, self.question_answering_prompt)

    def getMessagesHistory(self):

        return self.messages


    def start(self):
        query = "Is Enrique available on July 7th at 2:30 PM?"
        matching_docs = self.vectorstore.similarity_search(query)

        response = self.document_chain.invoke(
           {
               "context": matching_docs,
               "messages": [
                   HumanMessage(content=query)
               ]
           }
        )


        print(response)

if __name__ == "__main__":
    scheduler = MeetingSheduler()
    scheduler.start()
