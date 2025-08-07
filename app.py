from flask import Flask, render_template, request, jsonify
import os
from werkzeug.utils import secure_filename
from main import load_and_process_document, ask_question, add_document_to_vectordb, create_new_vectordb
import uuid

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Global variables to store the RAG system state
documents = []  # List of uploaded documents
vectordb = None  # Single vector database for all documents

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    global documents, vectordb
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    
    # Check file extension
    allowed_extensions = {'.txt', '.pdf', '.doc', '.docx'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        return jsonify({'success': False, 'error': f'Unsupported file type. Please upload: {", ".join(allowed_extensions)}'})
    
    if file:
        try:
            # Save the file
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Check if file is empty
            if os.path.getsize(filepath) == 0:
                os.remove(filepath)  # Clean up empty file
                return jsonify({'success': False, 'error': 'The uploaded file is empty'})
            
            # Add document to the collection
            if vectordb is None:
                # First document - create new vector database
                vectordb = create_new_vectordb(filepath, filename)
                documents.append({
                    'id': str(uuid.uuid4()),
                    'name': filename,
                    'path': filepath
                })
            else:
                # Add to existing vector database
                add_document_to_vectordb(vectordb, filepath, filename)
                documents.append({
                    'id': str(uuid.uuid4()),
                    'name': filename,
                    'path': filepath
                })
            
            return jsonify({
                'success': True, 
                'message': f'Document "{filename}" uploaded and added to your document collection! You now have {len(documents)} document(s) loaded.',
                'document_count': len(documents)
            })
            
        except ValueError as e:
            # Clean up the file if it was saved
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'success': False, 'error': str(e)})
        except Exception as e:
            # Clean up the file if it was saved
            if 'filepath' in locals() and os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'success': False, 'error': f'Error processing document: {str(e)}'})
    
    return jsonify({'success': False, 'error': 'Invalid file'})

@app.route('/ask', methods=['POST'])
def ask():
    global vectordb, documents
    
    if not vectordb or len(documents) == 0:
        return jsonify({'error': 'Please upload at least one document first'})
    
    data = request.get_json()
    question = data.get('question', '').strip()
    
    if not question:
        return jsonify({'error': 'Please provide a question'})
    
    try:
        # Get answer from RAG system
        answer = ask_question(question, vectordb, documents)
        return jsonify({'response': answer})
        
    except Exception as e:
        return jsonify({'error': f'Error processing question: {str(e)}'})

@app.route('/documents', methods=['GET'])
def get_documents():
    """Get list of uploaded documents"""
    global documents
    return jsonify({
        'documents': documents,
        'count': len(documents)
    })

@app.route('/clear-documents', methods=['POST'])
def clear_documents():
    """Clear all uploaded documents"""
    global documents, vectordb
    documents = []
    vectordb = None
    return jsonify({
        'success': True,
        'message': 'All documents cleared successfully!'
    })

@app.route('/status')
def status():
    global documents, vectordb
    return jsonify({
        'documents_loaded': len(documents) > 0,
        'document_count': len(documents),
        'documents': [doc['name'] for doc in documents]
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001) 