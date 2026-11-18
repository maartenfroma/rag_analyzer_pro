from rag_components.db_manager.db_connection import get_connection
from rag_components.models.doc_data_model import DocData
from rag_components.models.chat_data_model import ChatData

# Repository class for managing document records in the database
# save en get_all methoden voor documenten in de database
class DocumentRepository:

    @staticmethod
    def save(document: DocData):

        conn = get_connection()
        cursor=None
        
        try:
            if conn is None:
                print("No database connection")
                return
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO documents (
                    file_name,
                    file_size,
                    chunk_count,
                    embedding_model,
                    status
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    document.file_name,
                    document.file_size,
                    document.chunk_count,
                    document.embedding_model,
                    document.status
                )
            )

            document_id = cursor.fetchone()[0]

            conn.commit()

            return document_id

        finally:
            
            if cursor:
                cursor.close()
            if conn:
                conn.close()
            
            
    @staticmethod
    def get_all():

        conn = get_connection()
        cursor = None

        try:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    id,
                    file_name,
                    file_size,
                    chunk_count,
                    uploaded_at,
                    embedding_model,
                    status
                FROM documents
            """)

            # Return all rows as a list of tuples
            return cursor.fetchall()

        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()
    
   
    # Delete all document records from the database
    @staticmethod
    def delete_all():
        
        conn = get_connection()
        cursor = None

        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM documents")
            conn.commit()
            
            print("All documents have been deleted from the database.")
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()