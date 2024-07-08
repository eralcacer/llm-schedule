import openai
from openai import OpenAI
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage
from langchain.chains.question_answering import load_qa_chain

from dotenv import load_dotenv
# from google_drive import DriveAPI
import os

load_dotenv()

openai.api_key = os.getenv("OPEN_API_KEY")

chat = ChatOpenAI(model="gpt-3.5-turbo-0125")

class ChatMessage:
    def __init__(self, role, content):
        self.role = role
        self.content = content

class MeetingSheduler:
    def __init__(self):
        # self.drive_api = DriveAPI()
        self.chat_history = [("assistant","An appointment with Enrique on July 7th at 2:30 PM is created.")]
        
        self.loader = TextLoader("../content.txt")
        self.doc = self.loader.load()

        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=10)
        self.all_splits = self.text_splitter.split_documents(self.doc)
        
        self.vectorstore = Chroma.from_documents(documents=self.all_splits, embedding=OpenAIEmbeddings())
        self.output_parser = StrOutputParser()

        self.retriever = self.vectorstore.as_retriever()
        
        self.chain = load_qa_chain(chat, chain_type="stuff", verbose=True)

        self.retriever = self.vectorstore.as_retriever(k=4)

        # self.docs = self.retriever.invoke("Can LangSmith help test my LLM applications?")


        # user's new question goes to LLM and LLM reformulates the question with history
        self.contextualize_q_system_prompt = (
            """Given a chat history and the latest user question
            which might reference context in the chat history, formulate a standalone question
            which can be understood without the chat history. Do NOT answer the question,
            just reformulate it if needed and otherwise return it as is."""
        )
        
        self.contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.contextualize_q_system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
            ]
        )

        self.question_chain = self.contextualize_q_prompt | chat | StrOutputParser()

        self.template_rag = """
        Answer the user's questions based on the below context.
        Insert to the beginning of the response a way to indicate if the meeting could have been created or not with a "True" for yes or "False" for no.
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
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
            ]
        )
        
        self.retriever_chain = RunnablePassthrough.assign(
            context=self.contextualized_question | self.retriever
        )

        self.document_chain = create_stuff_documents_chain(chat, self.question_answering_prompt)

        self.rag_chain = (
                            self.retriever_chain
                          | self.question_answering_prompt
                          | chat
        )

    def contextualized_question(self, input: dict):
        if input.get("chat_history"):
            return self.question_chain
        else:
            return input["input"]

    def start(self):
        query = "Is Enrique available on July 7th at 2:30 PM?"

        response = self.rag_chain.invoke({"input": query, "chat_history": self.chat_history})
        self.chat_history.extend([HumanMessage(content=query), response])

        print(response.content)

if __name__ == "__main__":
    scheduler = MeetingSheduler()
    scheduler.start()
