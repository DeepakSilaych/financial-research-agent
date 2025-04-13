import os
import json
import fitz  # PyMuPDF
import base64
import asyncio
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI client
client = OpenAI()

# Get upload and data directories
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
DATA_DIR = os.getenv("DATA_DIR", "./data")

async def process_single_page_as_image(file_path, page_num):
    """
    Renders a full page as an image and extracts a textual description using OpenAI Vision.
    """
    chunks = []

    try:
        doc = fitz.open(file_path)
        page = doc.load_page(page_num)

        # Render full page as image
        pix = page.get_pixmap(dpi=200)
        image_bytes = pix.tobytes("png")
        base64_image = base64.b64encode(image_bytes).decode()

        # Send full-page image to OpenAI Vision
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": 
                            "You are a data extractor. This image is a page from a financial PDF. Extract all information in structured format as JSON or Markdown tables.\n\
                            - Include all tabular data, metrics, figures.\n\
                            - Preserve sections like 'Financial Highlights', 'Shareholding Pattern', etc.\n\
                            - Do NOT summarize. Just extract data.\n\
                            - Use Markdown tables or nested JSON arrays/objects if needed.\n\
                            - No interpretation, only extraction."},

                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
        )

        page_description = response.choices[0].message.content
        chunks.append(page_description)

    except Exception as e:
        print(f"Error processing page {page_num + 1} in file {file_path}: {e}")
    finally:
        doc.close()

    return chunks

async def process_pdf_file(file_path, output_dir):
    """
    Processes each page of a PDF as an image and saves the responses in a JSON file.
    """
    try:
        # Ensure file exists
        if not os.path.exists(file_path):
            print(f"❌ File {file_path} does not exist.")
            return None
            
        # Ensure it's a PDF file
        if not file_path.lower().endswith('.pdf'):
            print(f"❌ File {file_path} is not a PDF.")
            return None
            
        doc = fitz.open(file_path)
        total_pages = len(doc)
        doc.close()

        all_chunks = []
        # Process first 5 pages max to save API costs
        max_pages = min(total_pages, 5)
        for page_num in range(max_pages):
            page_chunks = await process_single_page_as_image(file_path, page_num)
            all_chunks.extend(page_chunks)

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Save the output JSON
        filename_wo_ext = os.path.splitext(os.path.basename(file_path))[0]
        output_path = os.path.join(output_dir, f"{filename_wo_ext}.json")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_chunks, f, indent=2, ensure_ascii=False)

        print(f"✅ Saved processed data to {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ Failed to process file {file_path}: {e}")
        return None

async def process_upload(file_path):
    """
    Process an uploaded file and create embeddings
    
    Args:
        file_path: The path to the uploaded file (relative to UPLOAD_DIR)
        
    Returns:
        str: Path to the embedding file or None if processing failed
    """
    try:
        # Get absolute file path
        abs_file_path = os.path.join(UPLOAD_DIR, file_path)
        
        # Ensure file exists
        if not os.path.exists(abs_file_path):
            print(f"❌ Upload file {abs_file_path} not found.")
            return None
            
        # Create embeddings directory for this file
        embedding_dir = os.path.join(DATA_DIR, "embeddings")
        os.makedirs(embedding_dir, exist_ok=True)
        
        # Process the file if it's a PDF
        if abs_file_path.lower().endswith(".pdf"):
            print(f"📄 Processing PDF file: {abs_file_path}")
            return await process_pdf_file(abs_file_path, embedding_dir)
        else:
            print(f"⚠️ File {abs_file_path} is not a PDF, skipping parsing.")
            return None
    except Exception as e:
        print(f"❌ Error in process_upload: {e}")
        return None

# For standalone usage
async def process_folder(folder_path):
    """
    Processes all PDF files in the folder as page images.
    """
    output_dir = os.path.join(DATA_DIR, "embeddings")
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".pdf"):
            file_path = os.path.join(folder_path, filename)
            print(f"📄 Processing {filename}...")
            await process_pdf_file(file_path, output_dir)

# For testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        pdf_folder_path = sys.argv[1]
    else:
        pdf_folder_path = "pdfs"  # Default folder containing PDFs
    
    print(f"Processing PDFs in folder: {pdf_folder_path}")
    asyncio.run(process_folder(pdf_folder_path))
