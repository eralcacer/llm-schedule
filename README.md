# LLM Scheduler

This is an assistant chat app that pulls a document with meetings from the cloud Google Drive and uses LangChain and Open AI API to identify if the user is available according to the data inputted by the user.

# What did I learn?

💡 I learned how to augment the generative AI knowledge with my information. (RAG)

💡 I learned to implement LangChain with context extraction from a document and a chat history to contextualize the current question from the user related to previous questions.

💡 I learned how to work with Google Drive API and give permissions to my app to interact with Google Docs and Calendar.

# Dependencies

- Dotenv
- OpenAI
- Chromadb
- Langchain: core, chroma, community, openai, text splitter, langsmith
- Google API: core, python client, auth, auth httplib2, oauthlib, common protos
