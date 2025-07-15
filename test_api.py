#!/usr/bin/env python3
"""
Test script for the Audio Denoiser API
"""

import requests
import os
import sys
import time

def test_health():
    """Test the health endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running on http://localhost:8000")
        return False
    return True

def test_denoise(file_path, model_type="dns48", dry=0.0):
    """Test the denoise endpoint"""
    print(f"\nTesting denoise endpoint with {file_path}...")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {'model_type': model_type, 'dry': str(dry)}
            
            print(f"Uploading file with model_type={model_type}, dry={dry}...")
            response = requests.post("http://localhost:8000/denoise", files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Denoising successful")
                print(f"Response: {result}")
                
                # Download the denoised file
                filename = result['filename']
                download_response = requests.get(f"http://localhost:8000/download/{filename}")
                
                if download_response.status_code == 200:
                    output_path = f"test_output_{filename}"
                    with open(output_path, 'wb') as f:
                        f.write(download_response.content)
                    print(f"✅ Downloaded denoised file: {output_path}")
                    return True
                else:
                    print(f"❌ Failed to download file: {download_response.status_code}")
                    return False
            else:
                print(f"❌ Denoising failed: {response.status_code}")
                print(f"Error: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Error during denoising: {str(e)}")
        return False

def test_reload_model():
    """Test the reload model endpoint"""
    print("\nTesting reload model endpoint...")
    try:
        response = requests.post("http://localhost:8000/reload-model?model_type=dns64")
        if response.status_code == 200:
            print("✅ Model reload successful")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Model reload failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error during model reload: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Audio Denoiser API Tests")
    print("=" * 50)
    
    # Test health endpoint
    if not test_health():
        print("\n❌ Health check failed. Please make sure the server is running.")
        print("Start the server with: cd server && python main.py")
        sys.exit(1)
    
    # Test denoising with a sample file
    # You can replace this with your own audio file
    test_file = "../voice/orgin.m4a"  # Using the existing audio file in the project
    
    if os.path.exists(test_file):
        test_denoise(test_file, "dns48", 0.0)
        test_denoise(test_file, "dns64", 0.0)
    else:
        print(f"\n⚠️  Test file not found: {test_file}")
        print("Please provide an audio file to test with:")
        print("python test_api.py <path_to_audio_file>")
        
        # If a file path is provided as argument, use it
        if len(sys.argv) > 1:
            test_file = sys.argv[1]
            if os.path.exists(test_file):
                test_denoise(test_file, "dns48", 0.0)
            else:
                print(f"❌ File not found: {test_file}")
    
    # Test model reload
    test_reload_model()
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")

if __name__ == "__main__":
    main() 