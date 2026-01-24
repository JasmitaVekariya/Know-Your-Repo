
import chromadb
import sys

def inspect_session(session_id):
    print(f"Inspecting session: {session_id}")
    try:
        client = chromadb.PersistentClient(path="./chroma_store")
        
        # List all collections
        collections = client.list_collections()
        print(f"\nFound {len(collections)} collections in ChromaDB:")
        for c in collections:
            print(f"- {c.name}")
            
        print("-" * 30)
        
        # Get specific collection
        try:
            collection = client.get_collection(name=session_id)
            count = collection.count()
            print(f"Collection '{session_id}' has {count} chunks.")
            
            if count > 0:
                print("\nSample chunks (first 3):")
                # Peek returns first n items
                pk = collection.peek(limit=3)
                
                ids = pk['ids']
                documents = pk['documents']
                metadatas = pk['metadatas']
                
                for i in range(len(ids)):
                    print(f"\nChunk ID: {ids[i]}")
                    print(f"Metadata: {metadatas[i]}")
                    print(f"Content Preview: {documents[i][:100]}...")
                    
        except ValueError:
             print(f"Collection '{session_id}' not found!")
             
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python inspect_chroma.py <session_id>")
    else:
        inspect_session(sys.argv[1])
