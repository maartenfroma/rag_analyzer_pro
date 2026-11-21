from typing import Any
from langchain_core.documents import Document
from streamlit import context
from rag_components.ai_assistants.gemini_ai_assistant import GeminiAssistant

from rag_components.exceptions.rag_exceptions import (
    ChatHistoryError,
    VectorStoreError,
    SimilaritySearchError,
    ContextGenerationError,
)
from rag_components.exceptions.gemini_exceptions import GeminiAuthenticationError

import logging

logger = logging.getLogger(__name__)


class RAGEngine:

    # Initialize the RAG engine with a GeminiAssistant instance and optional vector store
    def __init__(self, assistant: GeminiAssistant):
        self.assistant: GeminiAssistant = assistant

        if not assistant:
            raise GeminiAuthenticationError(
                "A GeminiAssistant instance must be provided."
            )

        logger.info("RAGEngine initialized with GeminiAssistant.")
        logger.info("Initializing vector stores and chat history.")

        # Initialize the vector stores list
        logger.info("Initializing RAGEngine components.")
        self.vector_stores: list = []

        # Initialize the chat history as a list of dictionaries
        self.chat_history: list[dict] = []

        # Store the last retrieved documents from the vector store
        self.last_retrieved_docs = []

    # Load a processors (e.g., vector store) into the RAG engine
    # Retrieve content from the vector store based on a query
    def load_processors(self, processors: Any) -> tuple[int, int]:

        self.vector_stores = []
        total_documents = 0
        total_chunks = 0

        for processor in processors:
            if not processor:
                continue
            if not hasattr(processor, "process"):
                continue

            result = processor.process()

            if result is None:
                print(f"Processor {processor} returned None, skipping.")
                print(f"{processor.__class__.__name__}")

            if result is None:
                continue

            vector_store, docs, chunks = result

            self.vector_stores.append(vector_store)

            total_documents += docs
            total_chunks += chunks

        logger.info("Total documents loaded: %d", total_documents)
        logger.info("Total chunks loaded: %d", total_chunks)
        
        # Returns the total number of documents and chunks loaded into the RAG engine
        # Data type: tuple[int, int] representing total documents and total chunks loaded
        return total_documents, total_chunks

    # Retrieve content from the vector store based on a query
    def retrieve_content(self, query: str, k: int = 10) -> str:

        # Check if the vector stores have been initialized before attempting retrieval
        if not self.vector_stores:
            raise VectorStoreError("Vector store is not loaded.")
        
        # Attempt to retrieve similar documents from each vector store
        try:
            
            # Initialize an empty list to store retrieved documents
            documents = []
            
            # Iterate over each vector store and perform similarity search
            for vs in self.vector_stores:
                # Perform similarity search on the current vector store
                docs = vs.similarity_search(query=query, k=k)
                # Log the number of documents retrieved from the current vector store
                logger.info("Retrieved %d documents from vector store", len(docs))
                documents.extend(docs)
        except Exception as e:
            logger.error("Error during similarity search: %s", e)
            raise SimilaritySearchError(
                "Failed to retrieve content from vector store."
            ) from e

        # Process the retrieved documents to remove duplicates and extract context information
        try:
            
            # Initialize a list to store unique documents and a set to track seen content
            unique_docs = []
            seen = set()

            context_parts = []
           

            # Iterate over each retrieved document and extract context information
            for doc in documents:
                logger.info("Metadata for document: %s", doc.metadata)

                # Skip documents that have already been seen to avoid duplicates    
                if doc.page_content not in seen:
                    unique_docs.append(doc)
                    seen.add(doc.page_content)

                    source = doc.metadata.get("file_name", "unknown")

                    # Extract the source file name from the document metadata
                    meta = []

                    # Collect metadata information for the current document
                    if "page" in doc.metadata:
                        meta.append(f"Page: {doc.metadata['page']}")
                    if "table" in doc.metadata:
                        meta.append(f"Table: {doc.metadata['table']}")

                    if "slide" in doc.metadata:
                        meta.append(f"Slide: {doc.metadata['slide']}")

                    if "start_time" in doc.metadata:
                        meta.append(f"Start Time: {doc.metadata['start_time']}")

                    if "end_time" in doc.metadata:
                        meta.append(f"End Time: {doc.metadata['end_time']}")

                    if "duration" in doc.metadata:
                        meta.append(f"Duration: {doc.metadata['duration']}")

                    if "index" in doc.metadata:
                        meta.append(f"Index: {doc.metadata['index']}")

                    # Get the page number for reference, defaulting to "?" if not available
                    page = doc.metadata.get("page", "?")

                    # Combine the metadata information into a single string for context 
                    meta_info = " | ".join(meta)

                    # Append the context information for the current document to the context parts list
                    context_parts.append(
                        f"Document: {source}"
                        f"{' | ' + meta_info if meta_info else ''}\n"
                        f"{doc.page_content}"
                    )
                    

            # Store the unique documents as the last retrieved documents
            # for reference
            self.last_retrieved_docs = unique_docs

            context = "\n\n".join(context_parts)
        except Exception as e:
            logger.error("Error during context generation: %s", e)
            raise ContextGenerationError("Failed to generate context.") from e

        # Return the generated context for the retrieved documents
        # Return type is a string containing the combined context for all retrieved documents
        return context

    def ask(
        self, query: str, k: int = 4, prompt: str | None = None, enable_serp: bool = False
    ) -> tuple[str, list[str]]:

        # Ask a question to the RAG engine and get a response based on retrieved context
        # Retrieve the context from the vector store based on the query
        context: str = self.retrieve_content(query, k=k)
        
        final_query = query
        
        if prompt:
            final_query = f"""{prompt}
            
            Question:
            
            {query}"""
            
            
            
        print("Retrieved context:\n", context)

        answer, sources = self.assistant.ask_with_context(
            query=final_query, context=context, enable_serp=enable_serp
        )

        # Append the query, answer, sources, and context to the chat history for reference
        self.chat_history.append({"query": query, "response": answer})

        # Return the answer and sources as a tuple for further processing or display
        return answer, sources

    # Get the chat history containing all queries and responses
    # Return the chat history as a list of dictionaries with query
    # and response keys

    def get_chat_history(self) -> list[dict]:
        # Return the chat history containing all queries, answers, sources, and contexts
        return self.chat_history

    def clear_chat_history(self) -> None:
        # Clear the chat history to start a new conversation
        self.chat_history.clear()

    def __str__(self) -> str:
        # Return a string representation of the RAG engine, including chat history
        return "\n".join(
            [
                f"Query: {entry['query']}\nResponse: {entry['response']}"
                for entry in self.chat_history
            ]
        )
