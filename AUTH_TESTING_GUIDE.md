# Authentication Testing Guide - StylistAI

This guide will help you test the complete signup and login flow for StylistAI.

## Current Status

✅ **Backend Ready:**
- Firebase Admin SDK initialized
- Authentication endpoints working
- Token verification implemented

✅ **Frontend Ready:**
- Firebase Client SDK configured
- Signup/Login forms created
- Token management implemented

✅ **Configuration Complete:**
- Firebase service account: `firebase-service-account.json`
- Project ID: `stylistai`
- Web API Key configured

---

## How Authentication Works

### Architecture

```
┌─────────────────────────────────────────────┐
│              User Browser                    │
│  (frontend/index.html - Firebase Client SDK)│
└──────────────┬──────────────────────────────┘
               │
               ↓ Sign Up / Login
┌─────────────────────────────────────────────┐
│         Firebase Authentication              │
│    (Managed by Google - firebase.com)       │
└──────────────┬──────────────────────────────┘
               │
               ↓ Returns ID Token (JWT)
┌─────────────────────────────────────────────┐
│       Frontend Stores Token                  │
│    localStorage.setItem('authToken', token)  │
└──────────────┬──────────────────────────────┘
               │
               ↓ API Requests with Token
┌─────────────────────────────────────────────┐
│         FastAPI Backend                      │
│   (Verifies token with Firebase Admin SDK)  │
└──────────────┬──────────────────────────────┘
               │
               ↓ Token Valid
┌─────────────────────────────────────────────┐
│      User Authenticated - Show Chat         │
└─────────────────────────────────────────────┘
```

---

## Testing Signup (Creating New Account)

### Step 1: Open the Application

1. Make sure the server is running:
   ```bash
   source venv/bin/activate
   PYTHONPATH=/Users/nikhilkumar/StylistAI python app/main.py
   ```

2. Open browser to: **http://localhost:8000**

3. You should see the StylistAI login page with purple gradient

### Step 2: Create Account

1. Click **"Sign Up"** link (below the Sign In button)

2. Fill in the registration form:
   - **Full Name:** Your Name
   - **Email:** test@example.com (or your real email)
   - **Password:** test123456 (minimum 6 characters)

3. Click **"Create Account"**

### Step 3: What Happens

When you click Create Account:

1. **Frontend calls Firebase:**
   ```javascript
   createUserWithEmailAndPassword(auth, email, password)
   ```

2. **Firebase creates the user** and returns an ID token

3. **Frontend stores token:**
   ```javascript
   localStorage.setItem('authToken', token)
   ```

4. **Frontend automatically switches to chat screen**

5. **You're logged in!** 🎉

### Expected Result

✅ Success message: "Account created successfully!"
✅ Automatically redirected to chat interface
✅ Your email shown in top-right corner
✅ Ready to chat with the AI agent

### Possible Errors

❌ **"Email already in use"**
- This email is already registered
- Use a different email or try logging in instead

❌ **"Password should be at least 6 characters"**
- Use a longer password

❌ **"Invalid email"**
- Check email format (must have @ and domain)

---

## Testing Login (Existing Account)

### Step 1: Return to Login Screen

If you're already logged in:
1. Click **"Logout"** button (top-right)
2. You'll return to the login page

### Step 2: Login

1. Make sure you're on the **"Sign In"** form (default view)

2. Enter your credentials:
   - **Email:** test@example.com
   - **Password:** test123456

3. Click **"Sign In"**

### Step 3: What Happens

1. **Frontend calls Firebase:**
   ```javascript
   signInWithEmailAndPassword(auth, email, password)
   ```

2. **Firebase verifies credentials** and returns ID token

3. **Frontend stores new token:**
   ```javascript
   localStorage.setItem('authToken', token)
   ```

4. **Redirected to chat screen**

### Expected Result

✅ Success message: "Logged in successfully!"
✅ Redirected to chat interface
✅ Session persists (stays logged in on refresh)

### Possible Errors

❌ **"Wrong password"**
- Password doesn't match
- Try again or reset password in Firebase Console

❌ **"User not found"**
- Email not registered
- Sign up first

❌ **"Too many attempts"**
- Account temporarily locked
- Wait a few minutes and try again

---

## Testing Chat with AI Agent

Once logged in, you can test the LangGraph agent:

### Quick Test Prompts

Click the quick prompt buttons or type:

1. **"What should I wear for a business casual meeting?"**
   - Tests basic query handling
   - Should return outfit recommendations

2. **"Suggest a weekend casual look"**
   - Tests different occasion handling

3. **"What are the current fashion trends?"**
   - Tests trend search functionality

### What to Expect

1. **Your message appears** on the right (blue background)

2. **Typing indicator shows** (three bouncing dots)

3. **Agent workflow runs** (3-10 seconds):
   - Analyzes your query
   - Retrieves your preferences (mock data for now)
   - Searches trends (mock data for now)
   - Generates recommendations with OpenAI GPT-4

4. **Agent response appears** on the left with:
   - Personalization note
   - Multiple recommendations
   - Confidence scores

---

## Testing Session Persistence

### Test 1: Page Refresh

1. While logged in, refresh the page (F5 or Cmd+R)
2. **Expected:** You should stay logged in (no need to login again)
3. **Why:** Token stored in localStorage persists across page loads

### Test 2: Close and Reopen Browser

1. Close the browser tab
2. Open a new tab and go to http://localhost:8000
3. **Expected:** You should still be logged in
4. **Why:** localStorage persists until explicitly cleared

### Test 3: Token Expiration

1. Firebase tokens expire after **1 hour**
2. After 1 hour, refresh the page
3. **Expected:** You'll be logged out and need to login again
4. **Why:** Token has expired and needs renewal

---

## Debugging Tips

### Check Browser Console

Press **F12** (or Cmd+Option+I on Mac) to open Developer Tools:

#### Look for Firebase Errors

```javascript
// Success
Firebase initialized successfully
User logged in: user@example.com

// Errors
Error: Invalid email
Error: Wrong password
Error: Network error
```

#### Check localStorage

In Console tab, type:
```javascript
localStorage.getItem('authToken')
```

If logged in, you should see a long JWT token string.

### Check Network Requests

1. Open Developer Tools → Network tab
2. Perform signup/login
3. Look for requests to:
   - `identitytoolkit.googleapis.com` (Firebase auth)
   - `localhost:8000/auth/me` (Your API)

### Check Backend Logs

In your terminal where the server is running, you should see:

```
INFO - Starting StylistAI API...
INFO - Firebase initialized successfully for project: stylistai
INFO - 127.0.0.1:56189 - "GET /auth/me HTTP/1.1" 200 OK
```

---

## Common Issues & Solutions

### Issue: "Firebase already initialized"

**Symptom:** Warning in console
**Cause:** Page reloaded, Firebase SDK reinitialized
**Solution:** This is normal, ignore it

### Issue: "Missing authentication token"

**Symptom:** 401 Unauthorized error
**Cause:** Token not sent in Authorization header
**Solution:**
1. Check if logged in
2. Clear localStorage and login again
3. Check browser console for errors

### Issue: "Invalid authentication token"

**Symptom:** 401 error, token expired
**Cause:** Token is older than 1 hour
**Solution:**
1. Logout and login again
2. Firebase will issue a new token

### Issue: "Failed to initialize Firebase"

**Symptom:** Error on startup, auth doesn't work
**Cause:** Firebase service account file missing or invalid
**Solution:**
1. Check `firebase-service-account.json` exists
2. Verify `FIREBASE_CREDENTIALS_PATH` in `.env`
3. Download fresh service account from Firebase Console

### Issue: "CORS policy error"

**Symptom:** Network errors in browser console
**Cause:** Frontend can't access backend API
**Solution:**
1. Check `CORS_ORIGINS` in `.env` includes `http://localhost:8000`
2. Restart the backend server

### Issue: Chat messages not sending

**Symptom:** Message doesn't appear or gets stuck
**Cause:** Backend API not accessible or OpenAI key missing
**Solution:**
1. Verify server is running: `curl http://localhost:8000/health`
2. Check `OPENAI_API_KEY` is set in `.env`
3. Check browser console for error messages

---

## Manual API Testing (Advanced)

### Get ID Token

After logging in, get your token from localStorage:

```javascript
// In browser console (F12)
localStorage.getItem('authToken')
```

Copy the token (starts with `eyJ...`)

### Test API Endpoints with cURL

```bash
# Set your token
export TOKEN="eyJhbGciOiJSUzI1NiIsImtpZCI6IjE..."

# Get current user
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"

# Get user profile
curl -X GET http://localhost:8000/auth/profile \
  -H "Authorization: Bearer $TOKEN"

# Save preferences
curl -X POST http://localhost:8000/auth/preferences \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "occasions": ["casual", "business_casual"],
    "fit_preferences": "fitted",
    "budget": "mid-range",
    "style_aesthetics": ["minimalist"],
    "colors": ["navy", "grey", "white"]
  }'

# Chat with agent
curl -X POST http://localhost:8000/styling/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What should I wear for a business meeting?"
  }'
```

---

## Security Notes

### ✅ What's Secure

- Passwords never sent to your backend
- Firebase handles password hashing
- Tokens are JWT signed by Firebase
- Backend verifies every token with Firebase

### ⚠️ For Development Only

- `FIREBASE_WEB_API_KEY` in frontend is okay (it's meant to be public)
- `firebase-service-account.json` must stay private
- Never commit service account to git (already in .gitignore)

### 🔒 For Production

- Use HTTPS everywhere
- Enable Firebase App Check
- Set up proper CORS origins
- Use environment-specific Firebase projects
- Rotate service account keys regularly

---

## Next Steps After Testing

Once signup/login is working:

1. ✅ **Test with real data:**
   - Save actual user preferences
   - Connect to PostgreSQL database
   - Store preferences persistently

2. ✅ **Add more auth features:**
   - Password reset
   - Email verification
   - Social login (Google, Facebook)

3. ✅ **Improve chat:**
   - Connect to real ChromaDB
   - Store conversation history
   - Add image upload

4. ✅ **Deploy:**
   - Deploy backend to GCP Cloud Run
   - Deploy frontend to Firebase Hosting
   - Use production Firebase project

---

## Quick Reference

### Key Files

```
├── frontend/index.html         # Frontend with Firebase Client SDK
├── app/api/auth.py            # Backend auth endpoints
├── app/core/security.py       # Firebase Admin SDK integration
├── app/core/dependencies.py   # Auth middleware
├── firebase-service-account.json  # Service account (keep private!)
└── .env                       # Configuration
```

### Key Endpoints

- `POST /auth/me` - Get current user
- `POST /auth/preferences` - Save preferences
- `GET /auth/profile` - Get complete profile
- `POST /styling/query` - Chat with agent
- `GET /health` - Server health check
- `GET /docs` - API documentation

### Environment Variables

```bash
FIREBASE_CREDENTIALS_PATH=./firebase-service-account.json
FIREBASE_PROJECT_ID=stylistai
FIREBASE_WEB_API_KEY=AIzaSyD...
OPENAI_API_KEY=sk-proj-...
```

---

## Success Checklist

Use this to verify everything is working:

- [ ] Server starts without errors
- [ ] Can access http://localhost:8000
- [ ] See login page with purple gradient
- [ ] Can create new account (signup)
- [ ] See success message after signup
- [ ] Automatically logged in after signup
- [ ] See chat interface after login
- [ ] Email shown in top-right corner
- [ ] Can send chat messages
- [ ] Agent responds with recommendations
- [ ] Can logout successfully
- [ ] Can login with existing account
- [ ] Session persists on page refresh
- [ ] Browser console has no errors

---

## Support

If you encounter issues:

1. Check this guide's troubleshooting section
2. Check browser console (F12) for errors
3. Check server logs in terminal
4. Verify all environment variables are set
5. Restart the server

**Your authentication system is ready to test!** 🚀

Try it now: http://localhost:8000
