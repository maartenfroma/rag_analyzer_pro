from typing import Any
from langchain_core.documents import Document
from rag_components.ai_assistants.gemini_ai_assistant import GeminiAssistant

class RAGEngine:

    # Initialize the RAG engine with a GeminiAssistant instance and optional vector store
    def __init__(self, assistant: GeminiAssistant):
        self.assistant: GeminiAssistant = assistant
        self.vector_store: Any | None = None
        self.chat_history: list[tuple[str, str]] = []  # Stores (query, response) pairs

    # Load a processor (e.g., vector store) into the RAG engine
    def load_processor(self, processor: Any) -> tuple[int, int]:

        # Process the given processor to obtain the vector store, document count, and chunk count
        vector_store, document_count, chunk_count = (processor.process())

        self.vector_store = vector_store

        # Store the vector store in the RAG engine instance
        return document_count, chunk_count

    
    #Retrieve content from the vector store based on a query
    def retrieve_content(
        self,
        query: str,
        k: int = 10
         ) -> str:

        if not self.vector_store:
            raise ValueError(
                "Vector store is not loaded."
            )

        documents: list[Document] = (
            self.vector_store.similarity_search(
                query,
                k=k
            )
        )

        for i, doc in enumerate(
            documents,
            start=1
        ):

            print(
                f"\nChunk {i} ..."
                f"{doc.page_content[:500]}"
            )

        context = "\n\n".join(
            doc.page_content
            for doc in documents
        )

        return context

    def ask(self, query: str, k: int = 10, enable_serp: bool = False) -> tuple[str, list[str]]:
        # Ask a question to the RAG engine and get a response based on retrieved context
        # Retrieve the context from the vector store based on the query
        context: str = self.retrieve_content(query, k=k)

        answer, sources = self.assistant.ask_with_context(query=query, context=context, enable_serp=enable_serp)

        # Append the query, answer, sources, and context to the chat history for reference
        self.chat_history.append((query, answer))
        

        # Return the answer and sources as a tuple for further processing or display
        return answer, sources


    def get_chat_history(self) -> list[tuple[str, str]]:
        # Return the chat history containing all queries, answers, sources, and contexts
        return self.chat_history

    def clear_chat_history(self) -> None:
        # Clear the chat history to start a new conversation
        self.chat_history.clear()

    def __str__(self) -> str:
        # Return a string representation of the RAG engine, including chat history
        return "\n".join([f"Query: {q}\nResponse: {r}" for q, r in self.chat_history])