from rag_components.db_manager.chat_repository import ChatRepository

chats = ChatRepository.get_all()

for chat in chats:
    print(chat)