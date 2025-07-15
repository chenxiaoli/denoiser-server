import logging
import os
# Add the parent directory to the path to import denoiser modules
import sys
import tempfile
import uuid
from typing import Optional

import torch
import torchaudio
import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from denoiser import enhance, pretrained

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Audio Denoiser API",
    description="RESTful API for audio denoising using Demucs models",
    version="1.0.0"
)

# Global model instance
model = None
device = "cpu"

class DenoiseRequest(BaseModel):
    model_type: Optional[str] = "dns48"  # dns48, dns64, master64, valentini_nc
    dry: Optional[float] = 0.0  # dry/wet knob coefficient
    device: Optional[str] = "cpu"

class DenoiseResponse(BaseModel):
    message: str
    filename: str

def load_model(model_type: str = "dns48", device: str = "cpu"):
    """Load the specified denoising model"""
    global model
    
    logger.info(f"Loading model: {model_type} on device: {device}")
    
    # Create a mock args object for the pretrained.get_model function
    class Args:
        def __init__(self, model_type, device):
            self.model_path = None
            self.dns48 = model_type == "dns48"
            self.dns64 = model_type == "dns64"
            self.master64 = model_type == "master64"
            self.valentini_nc = model_type == "valentini_nc"
            self.device = device
    
    args = Args(model_type, device)
    
    try:
        model = pretrained.get_model(args).to(device)
        model.eval()
        logger.info(f"Model {model_type} loaded successfully")
        return model
    except Exception as e:
        logger.error(f"Failed to load model {model_type}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")

def denoise_audio(audio_path: str, output_path: str, model_type: str = "dns48", dry: float = 0.0):
    """Denoise an audio file using the specified model"""
    global model
    
    if model is None:
        model = load_model(model_type, device)
    
    try:
        # Load the audio file
        noisy, sr = torchaudio.load(audio_path)
        
        # Ensure audio is mono and correct sample rate
        if noisy.shape[0] > 1:
            noisy = torch.mean(noisy, dim=0, keepdim=True)
        
        # Resample if necessary
        if sr != model.sample_rate:
            resampler = torchaudio.transforms.Resample(sr, model.sample_rate)
            noisy = resampler(noisy)
        
        # Add batch dimension if needed
        if noisy.dim() == 2:
            noisy = noisy.unsqueeze(0)
        
        # Move to device
        noisy = noisy.to(device)
        
        # Perform denoising
        with torch.no_grad():
            estimate = model(noisy)
            estimate = (1 - dry) * estimate + dry * noisy
        
        # Save the denoised audio
        estimate = estimate.squeeze(0)  # Remove batch dimension
        torchaudio.save(output_path, estimate.cpu(), model.sample_rate)
        
        logger.info(f"Denoising completed: {audio_path} -> {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error during denoising: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Denoising failed: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Initialize the model on startup"""
    global model, device
    
    # Check if CUDA is available
    if torch.cuda.is_available():
        device = "cuda"
        logger.info("CUDA available, using GPU")
    else:
        logger.info("CUDA not available, using CPU")
    
    # Load default model
    model = load_model("dns48", device)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Audio Denoiser API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    global model
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"status": "healthy", "model_loaded": model is not None, "device": device}

@app.post("/denoise")
async def denoise_file(
    file: UploadFile = File(...),
    model_type: Optional[str] = "dns48",
    dry: Optional[float] = 0.0
):
    """
    Denoise an audio file
    
    - **file**: Audio file to denoise (supports wav, mp3, m4a, etc.)
    - **model_type**: Model to use (dns48, dns64, master64, valentini_nc)
    - **dry**: Dry/wet knob coefficient (0 = only denoised, 1 = only input signal)
    """
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="File must be an audio file")
    
    # Validate model type
    valid_models = ["dns48", "dns64", "master64", "valentini_nc"]
    if model_type not in valid_models:
        raise HTTPException(status_code=400, detail=f"Invalid model type. Must be one of: {valid_models}")
    
    # Validate dry parameter
    if not 0 <= dry <= 1:
        raise HTTPException(status_code=400, detail="Dry parameter must be between 0 and 1")
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as temp_input:
        # Save uploaded file
        content = await file.read()
        temp_input.write(content)
        temp_input_path = temp_input.name
    
    # Create output file path
    unique_id = uuid.uuid4().hex
    output_filename = f"denoised_{unique_id}_{file.filename}"
    output_path = os.path.join(tempfile.gettempdir(), output_filename)
    
    try:
        # Perform denoising
        success = denoise_audio(temp_input_path, output_path, model_type, dry)
        
        if success:
            def iterfile():
                with open(output_path, "rb") as f:
                    yield from f
                # Clean up after streaming
                if os.path.exists(temp_input_path):
                    os.unlink(temp_input_path)
                if os.path.exists(output_path):
                    os.unlink(output_path)
            # Set media type based on output (wav)
            headers = {
                "Content-Disposition": f"attachment; filename={output_filename}"
            }
            return StreamingResponse(iterfile(), media_type="audio/wav", headers=headers)
        else:
            raise HTTPException(status_code=500, detail="Denoising failed")
            
    except Exception as e:
        # Clean up temporary files
        if os.path.exists(temp_input_path):
            os.unlink(temp_input_path)
        if os.path.exists(output_path):
            os.unlink(output_path)
        raise e


@app.post("/reload-model")
async def reload_model(model_type: str = "dns48"):
    """Reload the model with a different type"""
    global model
    
    try:
        model = load_model(model_type, device)
        return {"message": f"Model {model_type} loaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload model: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
