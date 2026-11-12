
import streamlit as st
import json

# Helper class to export chat history to the Streamlit session state
class ChatHistoryExporter:
    
    # Export a chat record to the Streamlit session state
    @staticmethod
    def export(question, answer, metadata=None):
        
        # Initialize chat history in the session state if it doesn't exist
        if "chat_history" not in st.session_state:
            st.session_state["chat_history"] = []
        
        # Create a new chat record with the question, answer, 
        # and optional metadata
        
        record={
            "question": question,
            "answer": answer,
            "metadata": metadata or []
        }
        
        # Append the new chat record to the chat history in the session state
        st.session_state["chat_history"].append(record)
   