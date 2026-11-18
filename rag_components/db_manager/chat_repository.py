from rag_components.db_manager.db_connection import get_connection
from rag_components.models.chat_data_model import ChatData

class ChatRepository:

    @staticmethod
    def save(chat: ChatData):

        conn = get_connection()
        cursor=None

        try:
            if conn is None:
                print("No database connection")
                return
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO chat_history (
                    question,
                    answer,
                    created_at
                )
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                (
                    chat.question,
                    chat.answer,
                    chat.created_at
                )
            )

            chat_id = cursor.fetchone()[0]

            conn.commit()

            return chat_id

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
            if conn is None:
                print("No database connection")
                return []
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, question, answer, created_at
                FROM chat_history
                ORDER BY created_at DESC
                """
            )

            rows = cursor.fetchall()
            chats = []
            for row in rows:
                chat = ChatData(
                    question=row[1],
                    answer=row[2],
                    created_at=row[3]
                )
                chats.append(chat)

            return chats

        finally:
            if cursor:
                cursor.close()

            if conn:
                conn.close()
                
                
    # Delete all chat records from the database
    @staticmethod
    def delete_all():
        conn = get_connection()
        cursor = None

        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat_history")
            conn.commit()
            
            print("All chat records have been deleted from the database.")
            
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()