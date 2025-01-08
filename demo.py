import modal

from fastapi import UploadFile, File, HTTPException
from fastapi.responses import JSONResponse


# Define the Docker image
docker_image = modal.Image.debian_slim().pip_install("fastapi", "requests", "docling")

# Create a Modal app
app = modal.App("modal-docling")

@app.function(
    image=docker_image,
    gpu="any", secrets=[modal.Secret.from_dotenv()]    
)
@modal.web_endpoint(method="POST", docs=True)
async def extract_markdown(file: UploadFile = File(...)):  
    import tempfile
    import os
    
    try:
        from docling.document_converter import DocumentConverter

    except ImportError:
        raise HTTPException(status_code=500, detail="docling package is not installed")
    if not file:  
        raise HTTPException(status_code=400, detail="No file part in the request")  
  
    if not file.filename:  
        raise HTTPException(status_code=400, detail="No file selected")  
  
    try:  
        # Save the uploaded file temporarily  
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:  
            contents = await file.read()  # Read the file contents asynchronously  
            temp_file.write(contents)  
            temp_file_path = temp_file.name  
  
        # Process the file using docling  
        converter = DocumentConverter()  
        result = converter.convert(temp_file_path)  
        markdown_content = result.document.export_to_markdown()  
  
        return JSONResponse(content={"markdown": markdown_content})  
    except Exception as e:  
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")  
    finally:  
        # Clean up the temporary file  
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):  
            os.unlink(temp_file_path)  
if __name__ == "__main__":
    with modal.enable_remote_debugging():
        with app.run():
            extract_markdown.remote()
