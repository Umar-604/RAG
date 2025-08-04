from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
import os

# Load and split the document
script_dir = os.path.dirname(os.path.abspath(__file__))
document_path = os.path.join(script_dir, "document", "sample.txt")
loader = TextLoader(document_path)
documents = loader.load()

print(f"Original document length: {len(documents[0].page_content)} characters")

# Better text splitting
text_splitter = CharacterTextSplitter(
    chunk_size=200,  # Smaller chunks for better precision
    chunk_overlap=20,  # Less overlap to avoid duplicates
    separator="\n"  # Split on paragraphs
)
texts = text_splitter.split_documents(documents)

print(f"Split into {len(texts)} text chunks")
for i, text in enumerate(texts):
    print(f"Chunk {i+1}: {text.page_content[:100]}...")

# Load embeddings
print("\nLoading embeddings model...")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Create vector DB
print("Creating vector database...")
vectordb = Chroma.from_documents(texts, embeddings, persist_directory="./vectordb")

# Load LLM for response refinement
print("Loading system...")
llm_available = False  # We'll use template-based responses instead

def refine_response(query, relevant_docs):
    """Create a professional response using template-based formatting"""
    if not relevant_docs:
        return "I couldn't find any relevant information in the document to answer your question."
    
    # Combine relevant documents
    context_parts = [doc.page_content for doc in relevant_docs]
    
    # Create a professional response template
    response = f"**Answer:**\n\n"
    
    # Extract key information and format it professionally
    for i, content in enumerate(context_parts, 1):
        # Clean up the content
        cleaned_content = content.strip()
        if cleaned_content:
            response += f"📄 **Source {i}:**\n{cleaned_content}\n\n"
    
    # Add a summary if we have multiple sources
    if len(context_parts) > 1:
        response += f"---\n"
        response += f"*This answer was compiled from {len(context_parts)} relevant sections of the document.*\n"
    else:
        response += f"---\n"
        response += f"*This information was retrieved from the document.*\n"
    
    return response

print("\n=== RAG System Ready! ===")
print("You can now ask questions about the document.")
print("Type 'quit' or 'exit' to stop the program.\n")

# Interactive question loop
retriever = vectordb.as_retriever(search_kwargs={"k": 3})  # Limit to top 3 results

while True:
    try:
        # Get user input
        query = input("Ask a question: ").strip()
        
        # Check for exit commands
        if query.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        if not query:
            print("Please enter a question.")
            continue
        
        print(f"\n🔍 Searching for: '{query}'")
        
        # Get relevant documents using the newer invoke method
        relevant_docs = retriever.invoke(query)
        
        if relevant_docs:
            print(f"📚 Found {len(relevant_docs)} relevant document sections")
            print("\n" + "="*60)
            print("💡 **REFINED ANSWER:**")
            print("="*60)
            
            # Get refined response
            refined_answer = refine_response(query, relevant_docs)
            print(refined_answer)
            
            print("\n" + "="*60)
        else:
            print("\n❌ No relevant documents found for your question.")
        
        print("\n" + "="*60 + "\n")
        
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        break
    except Exception as e:
        print(f"Error: {e}")
        print("Please try again.\n")
