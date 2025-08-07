# Image Quality Analyzer

## Overview

**Image Quality Analyzer** is a Python project that uses Azure OpenAI (GPT-4o or GPT-4 Vision) to evaluate the quality of images. It loads sample images from the `images` directory, encodes them, and sends them to an Azure OpenAI endpoint for automated assessment based on parameters such as brightness, graininess, exposure, and blurriness.

## Python Version

This project uses **Python 3.9**.  
Make sure you are running Python 3.9 or a compatible version.

## Installing Azure AI Foundry Libraries

To use Azure AI Foundry and related Azure AI services, install the required libraries using pip:

```bash
pip install azure-ai-ml
pip install azure-identity
pip install azure-ai-vision
pip install openai
```

> **Note:**  
> - `azure-ai-ml` is the main Azure AI Foundry SDK.
> - `azure-ai-vision` is for vision/image analysis.
> - `openai` is for Azure OpenAI GPT models.
> - You may need to upgrade pip: `pip install --upgrade pip`

## How It Works

- **Image Loading:** Reads all images in the `images` directory, converts them to bytes, and encodes them in base64.
- **Prompt Construction:** Sends each image to the Azure OpenAI model with a prompt instructing the model to evaluate image quality.
- **Response Handling:** The model returns a score for each parameter and a final decision (good or bad quality) for each image.
- **Sample Images:** The `images` directory contains sample images for demonstration and testing.

## Example Prompt

```
Evaluate the quality of images using the following Parameters:

Brightness: Overall lightness of the image.
Graininess: Presence of visual noise or texture irregularities.
Exposure: Balance of light and dark areas.
Blurriness: Sharpness and clarity of image details.

Scoring Criteria:
Each parameter should be scored on a scale from 1 (worst) to 10 (best).
If all four scores are below 6, classify each image as bad and recommend a retake. Else, determine the image is of good quality. Return in the response, the score for each parameter and the final decision.
```

## Deployment Plan

### 1. Azure Model Deployment

- Deploy a vision-capable model (e.g., GPT-4o or GPT-4 Vision) using Azure OpenAI Studio or Azure AI Foundry.
- Obtain the endpoint and API key for your deployment.
- Update the `.env` file with your `AOAI_ENDPOINT` and `AOAI_KEY`.

### 2. Productionalizing as an API

To make this solution consumable as a secure API:

1. **Wrap the logic in a web framework** (e.g., FastAPI or Flask).
2. **Add authentication** (e.g., OAuth2, API keys, or Azure AD).
3. **Deploy the API** to Azure (e.g., Azure App Service, Azure Functions, or Azure Container Apps).
4. **Restrict access** to authorized users/applications only.

#### Example: FastAPI Skeleton

```python
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from some_auth_module import authenticate_user  # Implement your auth logic

app = FastAPI()

@app.post("/analyze-image/")
async def analyze_image(file: UploadFile = File(...), user=Depends(authenticate_user)):
    # Read and process image, call OpenAI logic, return result
    pass
```

### 3. Best Practices

- **Environment Variables:** Store secrets in `.env` (never commit to source control).
- **Error Handling:** Ensure robust error handling for file I/O and API calls.
- **Logging:** Add logging for monitoring and debugging.
- **Scalability:** Use Azure Functions or Azure Container Apps for scalable deployments.
- **Security:** Always require authentication for API endpoints.

## Getting Started

1. Clone the repository.
2. Place sample images in the `images` directory.
3. Set up your `.env` file with Azure OpenAI credentials.
4. Run the main script to analyze images.

## Helpful Links

- [Azure OpenAI Service Documentation](https://learn.microsoft.com/en-us/azure/ai-services/openai/)
- [Azure AI Vision Documentation](https://learn.microsoft.com/en-us/azure/ai-services/computer-vision/)
- [Azure AI Foundry Documentation](https://learn.microsoft.com/en-us/azure/ai-studio/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Azure Deployment Best Practices](https://learn.microsoft.com/en-us/azure/developer/python/azure-sdk-best-practices)

---

**Note:**  
This project uses sample images in the `images` directory for demonstration. For production, ensure you follow Azure and security best practices for deployment