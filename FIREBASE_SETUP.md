# Firebase Authentication Setup Guide

This guide walks you through setting up Firebase Authentication for StylistAI.

## Step 1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click **"Add project"**
3. Enter project name: `stylistai` (or your preferred name)
4. Disable Google Analytics (optional)
5. Click **"Create project"**

## Step 2: Enable Authentication

1. In your Firebase project, click **"Authentication"** in the left sidebar
2. Click **"Get started"**
3. Go to **"Sign-in method"** tab
4. Enable **"Email/Password"** authentication
5. (Optional) Enable other providers: Google, Facebook, etc.

## Step 3: Get Service Account Credentials

### For Backend (FastAPI)

1. In Firebase Console, click the gear icon ⚙️ → **Project settings**
2. Go to **"Service accounts"** tab
3. Click **"Generate new private key"**
4. Download the JSON file
5. Save it as `firebase-service-account.json` in your project root
6. **IMPORTANT**: Add this file to `.gitignore` (already done)

### Get Project Details

From the **"General"** tab in Project settings:
- **Project ID**: Copy this value
- **Web API Key**: Copy this value

## Step 4: Configure Environment Variables

Create a `.env` file (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` and update Firebase settings:

```bash
# Firebase Authentication
FIREBASE_CREDENTIALS_PATH=./firebase-service-account.json
FIREBASE_PROJECT_ID=your-project-id-here
FIREBASE_WEB_API_KEY=AIza...your-web-api-key
```

## Step 5: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 6: Run the API

```bash
python app/main.py
# or
uvicorn app.main:app --reload
```

Visit: `http://localhost:8000/docs` to see API documentation

---

## How Authentication Works

### Frontend → Backend Flow

```
┌─────────────────────────────────────────────────┐
│          Frontend (React/Next.js/etc)           │
├─────────────────────────────────────────────────┤
│  1. User registers/logins via Firebase SDK      │
│  2. Firebase returns ID token                   │
│  3. Store token in localStorage/state           │
│  4. Include token in API requests               │
└──────────────────┬──────────────────────────────┘
                   │
                   ↓ Authorization: Bearer <token>
┌─────────────────────────────────────────────────┐
│          Backend (FastAPI - StylistAI)          │
├─────────────────────────────────────────────────┤
│  1. Extract token from Authorization header     │
│  2. Verify token with Firebase Admin SDK        │
│  3. Extract user info (uid, email, name)        │
│  4. Process request with user context           │
└─────────────────────────────────────────────────┘
```

---

## Frontend Integration Example

### Install Firebase SDK (Frontend)

```bash
npm install firebase
```

### Initialize Firebase (Frontend)

```javascript
// firebase-config.js
import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

const firebaseConfig = {
  apiKey: "YOUR_WEB_API_KEY",
  authDomain: "your-project-id.firebaseapp.com",
  projectId: "your-project-id",
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
```

### Register User (Frontend)

```javascript
import { createUserWithEmailAndPassword } from 'firebase/auth';
import { auth } from './firebase-config';

async function registerUser(email, password, name) {
  try {
    // Create user in Firebase
    const userCredential = await createUserWithEmailAndPassword(auth, email, password);

    // Get ID token
    const idToken = await userCredential.user.getIdToken();

    // Call your API to sync user profile
    const response = await fetch('http://localhost:8000/auth/me', {
      headers: {
        'Authorization': `Bearer ${idToken}`
      }
    });

    const userData = await response.json();
    console.log('User synced:', userData);

    return userData;
  } catch (error) {
    console.error('Registration error:', error);
  }
}
```

### Login User (Frontend)

```javascript
import { signInWithEmailAndPassword } from 'firebase/auth';
import { auth } from './firebase-config';

async function loginUser(email, password) {
  try {
    const userCredential = await signInWithEmailAndPassword(auth, email, password);
    const idToken = await userCredential.user.getIdToken();

    // Store token
    localStorage.setItem('authToken', idToken);

    return idToken;
  } catch (error) {
    console.error('Login error:', error);
  }
}
```

### Make Authenticated API Calls (Frontend)

```javascript
async function savePreferences(preferences) {
  const token = localStorage.getItem('authToken');

  const response = await fetch('http://localhost:8000/auth/preferences', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(preferences)
  });

  return await response.json();
}
```

---

## API Endpoints

### 1. Get Current User
```bash
GET /auth/me
Headers: Authorization: Bearer <firebase_id_token>

Response:
{
  "id": "firebase_uid",
  "email": "user@example.com",
  "name": "John Doe",
  "created_at": "2024-01-01T00:00:00",
  "is_active": true
}
```

### 2. Save Style Preferences
```bash
POST /auth/preferences
Headers: Authorization: Bearer <firebase_id_token>
Content-Type: application/json

Body:
{
  "occasions": ["casual", "business_casual"],
  "fit_preferences": "fitted",
  "budget": "mid-range",
  "style_aesthetics": ["minimalist", "modern"],
  "colors": ["navy", "grey", "white"]
}

Response:
{
  "user_id": "firebase_uid",
  "preferences": {...},
  "updated_at": "2024-01-01T00:00:00"
}
```

### 3. Get User Profile
```bash
GET /auth/profile
Headers: Authorization: Bearer <firebase_id_token>

Response:
{
  "uid": "firebase_uid",
  "email": "user@example.com",
  "name": "John Doe",
  "email_verified": true,
  "preferences": {...},
  "created_at": "2024-01-01T00:00:00"
}
```

---

## Testing with cURL

### 1. Get a Test Token

First, register/login a user using Firebase SDK or Firebase Auth UI, then get the ID token.

Or use the Firebase REST API:

```bash
# Register
curl -X POST \
  'https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=YOUR_WEB_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "test@example.com",
    "password": "test123456",
    "returnSecureToken": true
  }'

# Login
curl -X POST \
  'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=YOUR_WEB_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "test@example.com",
    "password": "test123456",
    "returnSecureToken": true
  }'
```

Copy the `idToken` from the response.

### 2. Test Your API

```bash
# Get current user
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_ID_TOKEN"

# Save preferences
curl -X POST http://localhost:8000/auth/preferences \
  -H "Authorization: Bearer YOUR_ID_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "occasions": ["casual"],
    "fit_preferences": "fitted",
    "budget": "mid-range",
    "style_aesthetics": ["minimalist"],
    "colors": ["black", "white"]
  }'
```

---

## Security Best Practices

1. **Never commit credentials**: `.gitignore` already excludes credential files
2. **Use environment variables**: All sensitive config in `.env`
3. **Token expiration**: Firebase ID tokens expire after 1 hour
4. **HTTPS in production**: Always use HTTPS for API and Firebase
5. **Validate tokens**: Backend verifies every token with Firebase
6. **Rate limiting**: Consider adding rate limiting (TODO)

---

## Troubleshooting

### "Firebase already initialized" error
- Normal on hot reload, can be ignored
- Firebase app is initialized once on startup

### "Invalid authentication token"
- Token may be expired (1 hour lifetime)
- Get a fresh token from Firebase SDK
- Check that token is included in Authorization header

### "Missing authentication token"
- Ensure `Authorization: Bearer <token>` header is set
- Token should not include "Bearer" when stored, add it in header

### Firebase initialization fails
- Check `FIREBASE_CREDENTIALS_PATH` points to correct file
- Verify JSON file is valid service account key
- Ensure `FIREBASE_PROJECT_ID` matches your project

---

## Next Steps

1. ✅ Firebase Authentication is set up
2. 🔄 Build outfit upload endpoints
3. 🔄 Implement styling recommendation engine
4. 🔄 Add GCS integration for images
5. 🔄 Set up ChromaDB for vector storage

