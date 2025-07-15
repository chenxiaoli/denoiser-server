# Audio Denoiser API

A FastAPI-based RESTful service for audio denoising using Demucs models. This service provides an easy-to-use API for removing noise from audio files.

## Features

- **Multiple Model Support**: Supports different pre-trained models (dns48, dns64, master64, valentini_nc)
- **GPU Acceleration**: Automatically uses CUDA if available
- **Flexible Audio Formats**: Supports various audio formats (wav, mp3, m4a, etc.)
- **Dry/Wet Control**: Adjustable dry/wet knob for mixing original and denoised audio
- **RESTful API**: Clean HTTP endpoints for easy integration

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure you have the denoiser module available (it should be in the parent directory).

## Usage

### Starting the Server

```bash
cd server
python main.py
```

The server will start on `http://localhost:8000`

### API Endpoints

#### 1. Health Check
```bash
GET /health
```
Returns the health status of the service and model loading status.

#### 2. Denoise Audio
```bash
POST /denoise
```
Upload an audio file for denoising.

**Parameters:**
- `file`: Audio file to denoise (multipart form data)
- `model_type`: Model to use (optional, default: "dns48")
  - `dns48`: DNS 48 model (default, fastest)
  - `dns64`: DNS 64 model (better quality)
  - `master64`: Master 64 model (best quality)
  - `valentini_nc`: Valentini non-causal model
- `dry`: Dry/wet knob coefficient (optional, default: 0.0)
  - `0.0`: Only denoised audio
  - `1.0`: Only original audio
  - Values between 0 and 1: Mix of both

**Response:**
```json
{
  "message": "Audio denoised successfully",
  "filename": "denoised_audio.wav"
}
```

#### 4. Reload Model
```bash
POST /reload-model?model_type=dns64
```
Reload the model with a different type.

### Example Usage with curl

1. **Denoise an audio file:**
```bash
curl -X POST "http://localhost:8000/denoise" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@noisy_audio.wav" \
  -F "model_type=dns64" \
  -F "dry=0.0"
```

2. **Download the denoised file:**
```bash
curl -X GET "http://localhost:8000/download/denoised_noisy_audio.wav" \
  --output denoised_audio.wav
```

3. **Check health:**
```bash
curl -X GET "http://localhost:8000/health"
```

### Example Usage with Python

```python
import requests

# Denoise an audio file
with open('noisy_audio.wav', 'rb') as f:
    files = {'file': f}
    data = {'model_type': 'dns64', 'dry': '0.0'}
    response = requests.post('http://localhost:8000/denoise', files=files, data=data)
    
if response.status_code == 200:
    result = response.json()
    filename = result['filename']
    
    # Download the denoised file
    download_response = requests.get(f'http://localhost:8000/download/{filename}')
    with open('denoised_audio.wav', 'wb') as f:
        f.write(download_response.content)
```

## API Documentation

Once the server is running, you can access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Model Information

- **dns48**: Fastest model, good for real-time processing
- **dns64**: Better quality than dns48, still relatively fast
- **master64**: Best quality, trained on multiple datasets
- **valentini_nc**: Non-causal model, good for offline processing

## Notes

- The service automatically detects and uses GPU if available
- Audio files are automatically converted to mono and resampled to 16kHz if needed
- Temporary files are automatically cleaned up after processing
- The model is loaded once at startup and reused for all requests

## Error Handling

The API returns appropriate HTTP status codes:
- `200`: Success
- `400`: Bad request (invalid parameters)
- `404`: File not found
- `500`: Internal server error (model loading or processing issues)
- `503`: Service unavailable (model not loaded)
