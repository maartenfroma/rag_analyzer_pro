from rag_components.db_manager.db_connection import get_connection



class DBCreateTable:
    
    
    @classmethod
    def create_table_documents(cls):
        
        
        conn = get_connection()
        cursor = conn.cursor() if conn else None
        if conn is None:
            print("No database connection")
            return
        create_table_sql = """
                            CREATE TABLE IF NOT EXISTS documents (
                            id SERIAL PRIMARY KEY,
                            file_name VARCHAR(255) NOT NULL,
                            file_size BIGINT DEFAULT 0,
                            chunk_count INTEGER DEFAULT 0,
                            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            embedding_model VARCHAR(100),
                            status VARCHAR(50)
                                )
                                """
                                
        try:
            cursor = conn.cursor() if conn else None
            
            if cursor is None:
                print("No database connection")
                return
            
            # Execute the SQL statement to create the table if it doesn't exist
            cursor.execute(create_table_sql)
            conn.commit()
            
            
        except Exception as e:
            print(f"Error creating table: {e}")
        
        # Close the cursor and connection if they were opened
        finally:
            if cursor:
                cursor.close()
                conn.close()
                
                
    @classmethod
    def create_table_chat(cls):
        
        conn = get_connection()
        cursor = conn.cursor() if conn else None
        
        if conn is None:
            print("No database connection")
            return
        
        create_table_sql = """
                           CREATE TABLE IF NOT EXISTS chat_history (
                                id SERIAL PRIMARY KEY,
                                question TEXT NOT NULL,
                                answer TEXT NOT NULL,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                                                            """
                                                            
        try:
            cursor = conn.cursor() if conn else None
            
            if cursor is None:
                print("No database connection")
                return
            
            cursor.execute(create_table_sql)
            conn.commit()
            
        except Exception as e:
            print(f"Error creating table: {e}")
        
        finally:
            if cursor:
                cursor.close()
                conn.close()
                                
                                
       