# Frontend Setup Guide - StylistAI Chat Interface

This guide will help you set up the static HTML/JS frontend for StylistAI with Firebase authentication and LangGraph agent chat.

## What's Included

The frontend provides:
- 🔐 **Firebase Authentication** (Sign up/Login)
- 💬 **Chat Interface** to interact with the LangGraph agent
- ⚡ **Real-time Styling Recommendations** from OpenAI + LangGraph
- 🎨 **Clean, Modern UI** with gradient background and smooth animations
- 📱 **Responsive Design** (works on desktop and mobile)

## Architecture

```
User Browser (frontend/index.html)
    ↓ [Firebase Auth]
Firebase Authentication Service
    ↓ [ID Token]
FastAPI Backend (localhost:8000)
    ↓ [Query + Context]
LangGraph Agent (langgraph_agent.py)
    ↓ [Styled Response]
OpenAI GPT-4
```

---

## Prerequisites

Before starting, ensure you have:

1. ✅ FastAPI backend running (from previous setup)
2. ✅ Virtual environment activated
3. ✅ Dependencies installed (including LangGraph)
4. ✅ Firebase project created
5. ✅ OpenAI API key in `.env`

---

## Setup Steps

### Step 1: Configure Environment Variables

Make sure your `.env` file has these values:

```bash
# Firebase Authentication
FIREBASE_CREDENTIALS_PATH=./firebase-service-account.json
FIREBASE_PROJECT_ID=stylistai  # Your Firebase project ID
FIREBASE_WEB_API_KEY=your-firebase-web-api-key-here  # Your web API key

# OpenAI (Required for LangGraph agent)
OPENAI_API_KEY=sk-proj-...your-actual-key...

# CORS (Allow frontend access)
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

### Step 2: Update Firebase Config in Frontend

Open `frontend/index.html` and update the Firebase configuration (line ~458):

```javascript
const firebaseConfig = {
    apiKey: "YOUR_FIREBASE_WEB_API_KEY",      // From .env
    authDomain: "YOUR_PROJECT_ID.firebaseapp.com",  // Replace YOUR_PROJECT_ID
    projectId: "YOUR_PROJECT_ID"              // From .env
};
```

**Where to find these values:**
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Click gear icon ⚙️ → Project Settings
4. Scroll to "Your apps" → Web app
5. Copy the config values

### Step 3: Enable Email/Password Authentication in Firebase

1. Go to Firebase Console → Authentication
2. Click "Get started" (if not already enabled)
3. Go to "Sign-in method" tab
4. Enable "Email/Password"
5. Save

### Step 4: Start the Backend

```bash
# Activate virtual environment
source venv/bin/activate

# Start FastAPI server
python app/main.py
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     StylistAI API started successfully
INFO:     Serving static files from: /path/to/frontend
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 5: Access the Frontend

Open your browser and go to:
```
http://localhost:8000
```

You should see the StylistAI login page!

---

## Using the Application

### 1. Create an Account

- Click "Sign Up" on the homepage
- Enter your name, email, and password (min. 6 characters)
- Click "Create Account"
- You'll be automatically logged in

### 2. Chat with the Agent

Once logged in, you'll see the chat interface. Try these prompts:

**Quick Prompts** (click the buttons):
- "What should I wear for a business casual meeting?"
- "Suggest a weekend casual look"
- "What are the current fashion trends?"

**Custom Prompts** (type your own):
- "I have a job interview tomorrow, what should I wear?"
- "Casual outfit for a first date?"
- "Help me update my wardrobe for winter"
- "What colors look good with navy blue?"

### 3. How the Agent Works

When you send a message, the LangGraph agent:

1. **Analyzes your query** - Understands what you're asking
2. **Retrieves your context** - Gets your preferences and past outfits (mock data for now)
3. **Searches trends** - Finds current fashion trends
4. **Generates recommendations** - Uses OpenAI GPT-4 to create personalized advice
5. **Returns styled response** - Shows recommendations with confidence scores

---

## Features

### Authentication
- ✅ Email/password signup
- ✅ Login with existing account
- ✅ Persistent sessions (stays logged in)
- ✅ Logout functionality
- ✅ Error handling (invalid credentials, weak passwords, etc.)

### Chat Interface
- ✅ Real-time messaging
- ✅ Typing indicators
- ✅ Quick prompt buttons
- ✅ Message history
- ✅ Smooth scrolling
- ✅ Professional styling

### Agent Features
- ✅ Multi-step workflow (analyze → retrieve → search → generate)
- ✅ Personalization based on user preferences
- ✅ Trend-aware recommendations
- ✅ Confidence scores for suggestions
- ✅ Stateful conversations

---

## API Endpoints Used

The frontend calls these backend endpoints:

### Authentication
- `POST /auth/me` - Get current user info

### Styling (LangGraph Agent)
- `POST /styling/query` - Send chat message, get recommendations
  ```json
  Request:
  {
    "query": "What should I wear for a business meeting?"
  }

  Response:
  {
    "query": "...",
    "recommendations": [...],
    "trends": [...],
    "personalization_note": "..."
  }
  ```

### Other Endpoints (for reference)
- `GET /docs` - API documentation
- `GET /health` - Health check
- `GET /styling/agent-status` - Check agent status

---

## Troubleshooting

### Issue: "Firebase already initialized" error
**Solution:** This is normal on page reload. Ignore it.

### Issue: "Invalid authentication token"
**Solution:**
- Token expired (1 hour lifetime) - Refresh the page to get a new token
- Check that Firebase is configured correctly
- Verify `FIREBASE_CREDENTIALS_PATH` is correct in `.env`

### Issue: "API error: 401"
**Solution:**
- Firebase auth token is invalid or expired
- Make sure you're logged in
- Refresh the page

### Issue: "API error: 500" or "Connection refused"
**Solution:**
- Backend is not running - Start with `python app/main.py`
- Check that the API is on `http://localhost:8000`
- Verify OpenAI API key is set in `.env`

### Issue: "Module 'app.api.styling' not found"
**Solution:**
- Make sure you created `app/api/styling.py`
- Check that `app/services/langgraph_agent.py` exists
- Verify all dependencies are installed: `pip install langchain langgraph langchain-openai`

### Issue: Frontend shows "404 Not Found"
**Solution:**
- Make sure `frontend/` directory exists
- Check that `frontend/index.html` is present
- Restart the FastAPI server

### Issue: "CORS policy" error in browser console
**Solution:**
- Update `CORS_ORIGINS` in `.env` to include your frontend URL
- Restart the backend server

### Issue: Agent responses are slow
**Solution:**
- Normal - OpenAI GPT-4 takes 3-10 seconds to respond
- Check your internet connection
- Consider using GPT-3.5 for faster responses (update `OPENAI_LLM_MODEL` in `.env`)

---

## Customization

### Change Colors/Theme

Edit the CSS in `frontend/index.html` (around line 10-230):

```css
/* Main gradient */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Primary color (buttons, headers) */
background: #667eea;
```

### Add More Quick Prompts

Edit the quick prompts section (around line 110):

```html
<button class="quick-prompt" onclick="sendQuickPrompt('Your prompt here')">
    Your Button Text
</button>
```

### Modify Agent Behavior

Edit `app/services/langgraph_agent.py`:
- Change workflow steps
- Add custom tools
- Modify prompts
- Adjust LLM temperature

---

## Next Steps

### Current Status
- ✅ Authentication working
- ✅ Chat interface functional
- ✅ LangGraph agent operational
- ⚠️ Using mock data for user preferences/history
- ⚠️ No image upload yet
- ⚠️ No persistent storage (PostgreSQL not connected)

### To Complete the POC

1. **Connect PostgreSQL**
   - Start Docker: `docker-compose up -d postgres`
   - Create database tables
   - Update `user_service.py` to use real database

2. **Connect ChromaDB**
   - Start Docker: `docker-compose up -d chromadb`
   - Implement vector embedding generation
   - Store outfit history in ChromaDB

3. **Add Image Upload**
   - Implement Google Cloud Storage integration
   - Add image analysis with Vision AI
   - Allow users to upload outfit photos

4. **Implement Real Data**
   - Replace mock data in `langgraph_agent.py`
   - Connect tools to actual databases
   - Add real trend search API

5. **Deploy to Production**
   - Deploy backend to GCP Cloud Run
   - Host frontend on Firebase Hosting or Vercel
   - Use production Firebase project

---

## Production Deployment

### Option 1: Deploy to Firebase Hosting (Frontend)

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login
firebase login

# Initialize
firebase init hosting

# Deploy
firebase deploy --only hosting
```

### Option 2: Deploy Backend to GCP Cloud Run

```bash
# Build Docker image
docker build -t gcr.io/YOUR_PROJECT/stylistai .

# Push to Google Container Registry
docker push gcr.io/YOUR_PROJECT/stylistai

# Deploy
gcloud run deploy stylistai \
  --image gcr.io/YOUR_PROJECT/stylistai \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

Update frontend `API_BASE_URL` to your Cloud Run URL.

---

## File Structure

```
StylistAI/
├── frontend/
│   └── index.html          # Complete single-page app
├── app/
│   ├── main.py            # FastAPI + static file serving
│   ├── api/
│   │   ├── auth.py        # Firebase auth endpoints
│   │   └── styling.py     # LangGraph chat endpoints
│   ├── services/
│   │   ├── langgraph_agent.py  # Multi-step agent workflow
│   │   └── user_service.py     # User management
│   └── models/
│       └── styling.py     # Pydantic schemas
├── .env                   # Configuration
└── requirements.txt       # Python dependencies
```

---

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review browser console for errors (F12)
3. Check FastAPI logs in terminal
4. Verify all environment variables are set
5. Ensure Firebase is properly configured

---

## Demo Tips

For a successful POC demo:

1. ✅ **Test before the demo** - Create an account and try several prompts
2. ✅ **Have OpenAI API credits** - GPT-4 calls cost money
3. ✅ **Prepare example prompts** - Use the quick prompt buttons
4. ✅ **Explain the workflow** - Show how the agent thinks step-by-step
5. ✅ **Highlight personalization** - Mention how it uses user preferences
6. ✅ **Show confidence scores** - Demonstrate AI transparency
7. ✅ **Discuss future features** - Image upload, outfit history, trends

Good luck with your POC! 🚀
