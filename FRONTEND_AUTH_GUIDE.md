# Frontend Authentication Implementation Guide

Complete guide for implementing authentication in your frontend with 5-day persistent login.

## Overview

- **Token Lifetime:** 5 days (7200 minutes)
- **Storage Options:** LocalStorage (recommended for SPAs) or Cookies
- **Auto-refresh:** Token automatically renewed on each request
- **Logout:** Clear stored credentials

---

## Quick Start (JavaScript/Elm)

### Option 1: LocalStorage (Recommended for SPAs)

**Pros:**
- Simple JavaScript API
- Works great with Elm ports
- No cookie configuration needed
- Large storage capacity (5-10MB)

**Cons:**
- Vulnerable to XSS attacks (use CSP headers)
- Not sent automatically with requests

### Option 2: Cookies

**Pros:**
- Can be HttpOnly (XSS protection)
- Automatically sent with requests
- Works across subdomains

**Cons:**
- Requires backend cookie support
- Smaller storage (4KB)
- CSRF protection needed

---

## Implementation: LocalStorage (Recommended)

### JavaScript Example

#### 1. Login Function

```javascript
// auth.js
const API_BASE_URL = 'http://localhost:8000';

async function login(username, password) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        username,
        password
      })
    });

    if (!response.ok) {
      throw new Error('Login failed');
    }

    const data = await response.json();

    // Store token in localStorage
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('token_type', data.token_type);
    localStorage.setItem('username', username);
    localStorage.setItem('login_time', Date.now());

    return data;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
}
```

#### 2. Authenticated API Calls

```javascript
async function fetchWithAuth(url, options = {}) {
  const token = localStorage.getItem('access_token');

  if (!token) {
    throw new Error('Not authenticated');
  }

  const headers = {
    ...options.headers,
    'Authorization': `Bearer ${token}`
  };

  const response = await fetch(url, {
    ...options,
    headers
  });

  // Handle token expiration
  if (response.status === 401) {
    // Token expired, redirect to login
    logout();
    window.location.href = '/login';
  }

  return response;
}

// Example usage
async function fetchVideos() {
  const response = await fetchWithAuth(`${API_BASE_URL}/api/videos`);
  return await response.json();
}
```

#### 3. Check if Logged In

```javascript
function isLoggedIn() {
  const token = localStorage.getItem('access_token');
  const loginTime = localStorage.getItem('login_time');

  if (!token || !loginTime) {
    return false;
  }

  // Check if token expired (5 days = 432000000 ms)
  const now = Date.now();
  const elapsed = now - parseInt(loginTime);
  const FIVE_DAYS_MS = 5 * 24 * 60 * 60 * 1000;

  if (elapsed > FIVE_DAYS_MS) {
    logout(); // Token expired
    return false;
  }

  return true;
}
```

#### 4. Logout Function

```javascript
function logout() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('token_type');
  localStorage.removeItem('username');
  localStorage.removeItem('login_time');
}
```

#### 5. Get Current User

```javascript
function getCurrentUser() {
  if (!isLoggedIn()) {
    return null;
  }

  return {
    username: localStorage.getItem('username'),
    token: localStorage.getItem('access_token')
  };
}
```

---

## Elm Integration (Ports)

### 1. Define Ports (Main.elm)

```elm
port module Main exposing (main)

-- Outgoing ports (Elm -> JavaScript)
port storeToken : { token : String, username : String } -> Cmd msg
port removeToken : () -> Cmd msg

-- Incoming ports (JavaScript -> Elm)
port tokenReceived : (Maybe String -> msg) -> Sub msg
```

### 2. JavaScript Port Handlers

```javascript
// index.js
const app = Elm.Main.init({
  node: document.getElementById('app')
});

// Store token in localStorage
app.ports.storeToken.subscribe(({ token, username }) => {
  localStorage.setItem('access_token', token);
  localStorage.setItem('username', username);
  localStorage.setItem('login_time', Date.now());
});

// Remove token from localStorage
app.ports.removeToken.subscribe(() => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('username');
  localStorage.removeItem('login_time');
});

// Send token to Elm on init
const token = localStorage.getItem('access_token');
const loginTime = localStorage.getItem('login_time');
const FIVE_DAYS_MS = 5 * 24 * 60 * 60 * 1000;

if (token && loginTime && (Date.now() - parseInt(loginTime) < FIVE_DAYS_MS)) {
  app.ports.tokenReceived.send(token);
} else {
  app.ports.tokenReceived.send(null);
}

// Intercept HTTP requests to add Authorization header
function fetchWithAuth(url, options = {}) {
  const token = localStorage.getItem('access_token');

  if (token) {
    options.headers = {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    };
  }

  return fetch(url, options);
}

// Make it available globally
window.fetchWithAuth = fetchWithAuth;
```

### 3. Elm Update Logic

```elm
type Msg
    = LoginSubmit
    | LoginResponse (Result Http.Error LoginData)
    | LogoutClicked
    | TokenReceived (Maybe String)

type alias Model =
    { token : Maybe String
    , username : Maybe String
    , loginForm : LoginForm
    }

update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        LoginSubmit ->
            ( model, loginUser model.loginForm )

        LoginResponse (Ok loginData) ->
            ( { model
                | token = Just loginData.access_token
                , username = Just model.loginForm.username
              }
            , storeToken
                { token = loginData.access_token
                , username = model.loginForm.username
                }
            )

        LoginResponse (Err _) ->
            ( model, Cmd.none )

        LogoutClicked ->
            ( { model | token = Nothing, username = Nothing }
            , removeToken ()
            )

        TokenReceived maybeToken ->
            ( { model | token = maybeToken }
            , Cmd.none
            )

-- Subscriptions
subscriptions : Model -> Sub Msg
subscriptions model =
    tokenReceived TokenReceived
```

### 4. HTTP Requests with Token

```elm
fetchVideos : Maybe String -> Cmd Msg
fetchVideos maybeToken =
    let
        headers =
            case maybeToken of
                Just token ->
                    [ Http.header "Authorization" ("Bearer " ++ token) ]

                Nothing ->
                    []
    in
    Http.request
        { method = "GET"
        , headers = headers
        , url = "http://localhost:8000/api/videos"
        , body = Http.emptyBody
        , expect = Http.expectJson VideosReceived videosDecoder
        , timeout = Nothing
        , tracker = Nothing
        }
```

---

## Implementation: Cookies (Alternative)

### JavaScript with Cookies

```javascript
// auth.js
async function login(username, password) {
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: new URLSearchParams({ username, password })
  });

  const data = await response.json();

  // Store in cookie (5 days)
  document.cookie = `access_token=${data.access_token}; max-age=${5 * 24 * 60 * 60}; path=/; SameSite=Strict; Secure`;
  document.cookie = `username=${username}; max-age=${5 * 24 * 60 * 60}; path=/; SameSite=Strict; Secure`;

  return data;
}

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

function getToken() {
  return getCookie('access_token');
}

function logout() {
  document.cookie = 'access_token=; max-age=0; path=/';
  document.cookie = 'username=; max-age=0; path=/';
}

async function fetchWithAuth(url, options = {}) {
  const token = getToken();

  const headers = {
    ...options.headers,
    'Authorization': `Bearer ${token}`
  };

  return fetch(url, { ...options, headers });
}
```

⚠️ **Note:** For production, use `HttpOnly` cookies which require backend support. The above example uses JavaScript-accessible cookies for simplicity.

---

## Security Best Practices

### 1. Content Security Policy (CSP)

Add to your HTML `<head>`:

```html
<meta http-equiv="Content-Security-Policy"
      content="default-src 'self'; script-src 'self' 'unsafe-inline'; connect-src 'self' https://api.bestvideoproject.com">
```

### 2. XSS Protection

```javascript
// Never use eval or innerHTML with user data
// Bad:
element.innerHTML = userInput;

// Good:
element.textContent = userInput;
```

### 3. Token Expiration Handling

```javascript
async function fetchWithAuth(url, options = {}) {
  const token = localStorage.getItem('access_token');
  const loginTime = localStorage.getItem('login_time');

  // Check expiration before making request
  if (!token || !loginTime) {
    redirectToLogin();
    return;
  }

  const elapsed = Date.now() - parseInt(loginTime);
  const FIVE_DAYS_MS = 5 * 24 * 60 * 60 * 1000;

  if (elapsed > FIVE_DAYS_MS) {
    logout();
    redirectToLogin();
    return;
  }

  // Make request
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`
    }
  });

  // Handle 401 (server-side expiration)
  if (response.status === 401) {
    logout();
    redirectToLogin();
  }

  return response;
}
```

### 4. HTTPS Only

```javascript
// Check if running on HTTPS in production
if (location.protocol !== 'https:' && location.hostname !== 'localhost') {
  location.replace(`https:${location.href.substring(location.protocol.length)}`);
}
```

---

## Complete Login Page Example

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Login - Best Video Project</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      max-width: 400px;
      margin: 100px auto;
      padding: 20px;
    }
    .form-group {
      margin-bottom: 15px;
    }
    label {
      display: block;
      margin-bottom: 5px;
    }
    input {
      width: 100%;
      padding: 8px;
      border: 1px solid #ddd;
      border-radius: 4px;
    }
    button {
      width: 100%;
      padding: 10px;
      background: #007bff;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
    }
    button:hover {
      background: #0056b3;
    }
    .error {
      color: red;
      margin-top: 10px;
    }
  </style>
</head>
<body>
  <h1>Login</h1>
  <form id="loginForm">
    <div class="form-group">
      <label for="username">Username</label>
      <input type="text" id="username" required>
    </div>
    <div class="form-group">
      <label for="password">Password</label>
      <input type="password" id="password" required>
    </div>
    <button type="submit">Login</button>
    <div id="error" class="error"></div>
  </form>

  <script>
    const API_BASE_URL = 'http://localhost:8000';

    document.getElementById('loginForm').addEventListener('submit', async (e) => {
      e.preventDefault();

      const username = document.getElementById('username').value;
      const password = document.getElementById('password').value;
      const errorDiv = document.getElementById('error');

      try {
        const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: new URLSearchParams({ username, password })
        });

        if (!response.ok) {
          throw new Error('Invalid credentials');
        }

        const data = await response.json();

        // Store in localStorage
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('username', username);
        localStorage.setItem('login_time', Date.now());

        // Redirect to main app
        window.location.href = '/';

      } catch (error) {
        errorDiv.textContent = error.message;
      }
    });

    // Check if already logged in
    if (localStorage.getItem('access_token')) {
      const loginTime = parseInt(localStorage.getItem('login_time'));
      const FIVE_DAYS_MS = 5 * 24 * 60 * 60 * 1000;

      if (Date.now() - loginTime < FIVE_DAYS_MS) {
        window.location.href = '/';
      }
    }
  </script>
</body>
</html>
```

---

## Testing

### Test Login

```javascript
// Open browser console
async function testLogin() {
  const response = await fetch('http://localhost:8000/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      username: 'reuben',
      password: 'bestvideoproject'
    })
  });

  const data = await response.json();
  console.log('Token:', data.access_token);

  localStorage.setItem('access_token', data.access_token);
  console.log('Token stored!');
}

testLogin();
```

### Test Authenticated Request

```javascript
async function testAuthRequest() {
  const token = localStorage.getItem('access_token');

  const response = await fetch('http://localhost:8000/api/videos', {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  const data = await response.json();
  console.log('Videos:', data);
}

testAuthRequest();
```

---

## Troubleshooting

### Token not persisting across page reloads

**Cause:** localStorage not being set

**Solution:** Check browser console for errors, ensure you're calling `localStorage.setItem` after successful login

### 401 Unauthorized errors

**Cause:** Token expired or invalid

**Solution:**
1. Check if token is still in localStorage: `localStorage.getItem('access_token')`
2. Verify token hasn't expired (check `login_time`)
3. Try logging in again

### CORS errors

**Cause:** Frontend and backend on different domains

**Solution:** Backend CORS is already configured for localhost. For production, update `backend/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourfrontend.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Summary

✅ **LocalStorage Implementation:**
- Store token after login
- Include `Authorization: Bearer <token>` header in all requests
- Check expiration before each request
- Clear storage on logout

✅ **5-Day Persistent Login:**
- Token valid for 7200 minutes (5 days)
- Store `login_time` to check client-side expiration
- Auto-logout when expired

✅ **Security:**
- Use HTTPS in production
- Implement CSP headers
- Handle 401 errors gracefully
- Never expose tokens in URLs or logs

Need help? Check the test examples above or review `AUTHENTICATION.md` for complete API documentation.
