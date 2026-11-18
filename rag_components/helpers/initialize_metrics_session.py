import streamlit as st

def initialize_metrics_session():
    
    # Initialize the metrics session in Streamlit
    defaults = {
        
        "chunks": 0,
        "file_size": 0,
        "current_filename": "",
        "docs": []
    
    }
    
    # Set default values for each key in the session state if not already set
    for key, value in defaults.items():
        
        # If the key is not already in the session state, set it to the default value
        if key not in st.session_state:
            st.session_state[key] = value
            
            
def delete_all():
    
    # Delete all metrics-related keys from the session state
    # Call this function to remove all metrics-related session state keys when needed
    
    keys_to_delete = ["chunks", "file_size", "current_filename", "docs"]
    
    # Iterate over each key and delete it from the session state if it exists   
    for key in keys_to_delete:
        
        # Check if the key exists in the session state before attempting to delete it
        if key in st.session_state:
            del st.session_state[key]   
