# Ngrok Setup for Local Development

This allows Replicate API to access your locally generated images.

## Steps:

1. **Start ngrok** (in a new terminal):
   ```bash
   ngrok http 8000
   ```

2. **Copy the ngrok URL** from the output:
   - Look for a line like: `Forwarding https://abc123.ngrok.io -> http://localhost:8000`
   - Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

3. **Update `.env` file**:
   - Open `backend/.env`
   - Set `NGROK_URL=https://abc123.ngrok.io` (replace with your actual ngrok URL)

4. **Restart the backend server**:
   - Stop the current backend (Ctrl+C)
   - Start it again: `cd backend && uv run python main.py`

## How it works:

- When `NGROK_URL` is set, the backend will return full ngrok URLs for images
- Example: Instead of `/api/images/6/data`, it returns `https://abc123.ngrok.io/api/images/6/data`
- Replicate can now access these URLs to download your images

## Testing:

1. Generate an image using the Image Models page
2. Click "Create Video from This Image" in the image gallery modal
3. The video generation should now work with the publicly accessible image URL

## Notes:

- Ngrok URLs change each time you restart ngrok (unless you have a paid plan)
- You'll need to update `NGROK_URL` in `.env` each time you restart ngrok
- Remove or empty `NGROK_URL` when deploying to production
