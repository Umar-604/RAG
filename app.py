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
