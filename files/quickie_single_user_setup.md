# Single User MVP Setup: Quickie Test Environment

**Goal:** Build, deploy, and test Quickie with just you as the user — with $0/month cost, no billing setup required  
**Timeline:** ~4 weeks to working MVP  
**Approach:** Free tiers only, no credit card required

**Your accounts (confirmed):**
- GitHub: `a-popa-apps`, repo `music-app`
- Hugging Face: `a-popa-music-apps` — **not used** (Docker SDK requires a paid plan; see Part 2)
- Vercel: connected
- Spotify Developer: created

---

## Part 1: CONFIRMED Tech Stack (TL;DR)

### Frontend
```
Framework: React 18 + TypeScript
Build Tool: Vite
CSS: Tailwind CSS
Deployment: Vercel
Host: Free tier (no card required)
```

### Backend
```
Runtime: Render (native Python 3.11 web service, no Docker needed)
Trigger: HTTP endpoint (FastAPI)
Host: Free tier (no card required)
```

### Audio Processing
```
BPM Detection: librosa (free, open-source)
Key Detection: essentia (free, open-source)
Genre Classification: Spotify API (free tier, non-commercial)
ID3 Tag Writing: mutagen (free, open-source)
```

### File Storage
```
None. Uploaded files are not retained.
Processing happens synchronously in a local temp directory for
the duration of a single request; the ZIP result is streamed
back in the response and the temp files are discarded after.
```

### Database
```
MVP Phase: NONE (stateless processing)
Phase 2: Firebase Firestore (free tier)
```

**FINAL STACK = 100% free tier, no billing setup, for single user testing ✅**

---

## Part 2: Complete Services Signup Checklist

Sign up for these in order. **Total accounts to create: 4**

### 1️⃣ GitHub (Code Hosting) — ✅ done
**Account:** `a-popa-apps`, repo `music-app`

**Free Tier Limits:**
- ✅ Unlimited public/private repos
- ✅ Unlimited collaborators
- ✅ Free GitHub Actions (2,000 minutes/month)

---

### 2️⃣ Vercel (Frontend Hosting) — ✅ done
**Service:** Vercel  
**Cost:** Free tier ✅

**What's left:**
- [ ] Import the `music-app` repository, point it at the `frontend/` subfolder
- [ ] Confirm auto-deploy on push works
- [ ] Note your deployment URL (e.g., `music-app.vercel.app`)

**Free Tier Limits:**
- ✅ Unlimited deployments
- ✅ Free SSL/HTTPS
- ✅ 100GB bandwidth/month (way more than you'll use)
- ✅ Global CDN included

**Monthly Cost: $0**

---

### 3️⃣ Render (Backend Hosting)
**Service:** Render (native Python runtime, no Docker)  
**Cost:** Free tier ✅, no credit card required  
**Why:** Run the Python audio-processing backend as an HTTP endpoint. We tried Hugging Face Spaces, but its Docker SDK requires a paid plan — Render's plain Python web service is free and doesn't need Docker at all.  
**Signup URL:** https://render.com

**What to do:**
- [ ] Create Render account (sign in with GitHub)
- [ ] Click "New" → "Web Service"
- [ ] Connect the `music-app` GitHub repo
- [ ] Root directory: `backend`
- [ ] Runtime: Python 3
- [ ] Build command: `pip install -r requirements.txt`
- [ ] Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [ ] Instance type: **Free**
- [ ] Click "Create Web Service" — Render builds and deploys automatically
- [ ] Note the endpoint URL (e.g., `https://music-app-backend.onrender.com`)

**Free Tier Limits:**
- ✅ 512MB RAM, 0.1 CPU (enough for single-user, one-file-at-a-time processing)
- ✅ No credit card required
- ⚠️ Spins down after 15 minutes of inactivity — cold start of ~30-60s on the next request
- ⚠️ 750 free instance-hours/month (more than enough for solo use)

**Monthly Cost: $0**

---

### 4️⃣ Spotify Developer Account (Optional, Genre Detection) — ✅ done
**Service:** Spotify Web API  
**Cost:** Free tier ✅

**What's left:**
- [ ] Copy Client ID and Client Secret
- [ ] Save as environment variables in Render (Dashboard → your service → Environment)

**Note:** Spotify's terms say "non-commercial" — DJ music organization is a gray area, but for MVP/testing it's fine. If you commercialize, you may need to negotiate with Spotify.

**Monthly Cost: $0**

---

### 5️⃣ Firebase (Phase 2 - Not Yet Needed)
**Service:** Firebase (Google's BaaS)  
**Cost:** Free tier ✅  
**Why:** User authentication, Firestore database for user accounts (Phase 2)  
**Signup URL:** https://console.firebase.google.com

**For MVP Phase 1:** SKIP THIS - Not needed yet  
**For Phase 2:** Sign up when you add user accounts

**Free Tier Limits:**
- ✅ Firestore: 50k reads/day
- ✅ Authentication: Unlimited users
- ✅ Hosting: 1GB storage

**Monthly Cost: $0 (free tier)**

---

## Part 3: Services Summary Table

| Service | Purpose | Cost | Signup URL | Status |
|---------|---------|------|-----------|--------|
| **GitHub** | Code hosting + version control | Free | github.com | ✅ Done |
| **Vercel** | Frontend deployment | Free | vercel.com | ✅ Done |
| **Render** | Backend audio processing | Free | render.com | ⏳ Needed |
| **Spotify API** | Genre detection | Free | developer.spotify.com | ✅ Done (optional) |
| **Firebase** | User accounts + DB | Free | firebase.google.com | ⏳ Phase 2 |

**Total Services: 4 (3 required, 1 optional, 1 later)**  
**Total Cost for MVP: $0 — no billing setup or credit card needed anywhere**

---

## Part 4: Signup Order (Step-by-Step)

### Remaining setup (~15 minutes)

**Step 1: Create Render Account & Web Service**
1. Go to https://render.com and sign up with GitHub
2. Click "New" → "Web Service"
3. Select the `music-app` repo (authorize Render to access it if prompted)
4. Root directory: `backend`
5. Runtime: Python 3
6. Build command: `pip install -r requirements.txt`
7. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
8. Instance type: Free
9. Click "Create Web Service"

**Step 2: Add Spotify secrets to Render**
1. In Render → your service → "Environment"
2. Add `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET`

**Step 3: Confirm Vercel is pointed at `frontend/`**
1. Vercel dashboard → your project → Settings → General → Root Directory → `frontend`

---

## Part 5: Deployment Architecture (Single User)

```
┌─────────────────────────────────────────────────────┐
│                   YOUR COMPUTER                      │
│  (npm run dev — local testing)                       │
└───────────────┬─────────────────────────────────────┘
                │
                │ git push
                ▼
        ┌───────────────┐
        │ GitHub Repo   │
        │ music-app     │
        └───────────────┘
                │
        auto-trigger (both watch the same repo)
                │
        ┌───────┴────────┐
        ▼                 ▼
┌───────────────┐  ┌───────────────────────────┐
│ Vercel        │  │ Render                     │
│ (frontend/)   │  │ (backend/, Python/FastAPI) │
│ music-app     │  │ audio processing:           │
│ .vercel.app   │  │ BPM / key / genre / tags    │
└───────┬───────┘  └─────────────┬─────────────┘
        │                        │
        │      API calls         │
        └───────────►────────────┘
                                  │
                     process in a local temp dir
                     for the request only, then
                     stream ZIP back and discard
```

**No persistent storage layer.** Uploaded files exist only in memory/temp disk for the duration of a single request and are never written to a database or bucket.

**Cost Breakdown (Single User):**
- Vercel: $0 (free tier)
- Render: $0 (free web service tier)
- Spotify API: $0 (free tier)
- GitHub: $0 (free tier)
- **TOTAL: $0/month, no credit card on file anywhere**

---

## Part 6: Local Development Setup

### Install Required Tools

**1. Node.js & npm**
```bash
# Download from https://nodejs.org (LTS version)
# Verify installation
node --version  # Should be v18+
npm --version   # Should be v9+
```

**2. Python 3.11**
```bash
# Download from https://python.org
# Verify
python3 --version  # Should be 3.11+

# Install audio libraries (for testing locally)
pip install librosa essentia mutagen spotipy fastapi uvicorn
```

No Docker or cloud CLI needed — Render builds directly from your `requirements.txt`.

---

## Part 7: Project Structure (Ready to Code)

```
music-app/                         (GitHub repo)
│
├── frontend/                      (React app, deployed to Vercel)
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── vercel.json                (Vercel config)
│
├── backend/                       (Python app, deployed to Render)
│   ├── app/
│   │   ├── main.py                (FastAPI entry point)
│   │   ├── process_audio.py       (Main logic)
│   │   ├── detect_bpm.py
│   │   ├── detect_key.py
│   │   ├── classify_genre.py
│   │   └── create_zip.py
│   └── requirements.txt           (Python dependencies)
│
├── docs/
│   ├── API.md                     (Function endpoints)
│   ├── DEPLOYMENT.md              (Step-by-step deploy)
│   └── LOCAL-SETUP.md
│
└── README.md
```

---

## Part 8: Deployment Process (3 Simple Steps)

### Step 1: Push to GitHub

```bash
# From the repo root
git add .
git commit -m "Initial commit"
git push origin main
```

**Result:** Vercel auto-deploys `frontend/`, and Render auto-deploys `backend/` — both watch the same repo and trigger on push.

### Step 2: Connect Frontend to Backend

In your React code:

```typescript
// src/services/api.ts
const BACKEND_URL = "https://music-app-backend.onrender.com/process";

export async function uploadAndProcess(files: File[]) {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));

  const response = await fetch(BACKEND_URL, {
    method: 'POST',
    body: formData
  });

  return response.blob(); // ZIP file
}
```

### Step 3: Test End-to-End

1. Go to your Vercel URL
2. Upload an MP3 file
3. Watch processing happen (first request may take 30-60s if Render's free instance was asleep)
4. Download the ZIP
5. Open ZIP → verify files have ID3 tags with BPM, Key, Genre

---

## Part 9: Free Tier Monitoring (Don't Get Surprised)

**Vercel:**
1. Dashboard → Settings → Billing
2. Already alerts you if approaching limits

**Render:**
1. Free tier has no billing to monitor — nothing is charged unless you explicitly upgrade the instance type
2. The free instance sleeps after 15 min idle; expect a cold-start delay on the next request

**GitHub:**
1. No alerts needed (free tier has no limits for solo users)

---

## Part 10: Testing Checklist (Single User)

### MVP (Phase 1) Testing Scope

You'll test these yourself:

**✅ File Upload**
- [ ] Drag-drop 1 MP3 file
- [ ] Works on mobile (your phone)
- [ ] Shows loading state
- [ ] File is valid

**✅ Audio Processing**
- [ ] BPM detected correctly (compare to known track)
- [ ] Key detected correctly (listen to track, verify key)
- [ ] Genre looks reasonable
- [ ] Process completes in <30 seconds (plus cold-start delay if Render was idle)

**✅ Export**
- [ ] ZIP downloads
- [ ] ZIP contains all files with ID3 tags
- [ ] .m3u8 playlist file is valid
- [ ] Files import into Rekordbox (if you have it)

**✅ Edge Cases**
- [ ] Upload 2GB file → Get error message
- [ ] Upload 50 files → Get error message (25 limit)
- [ ] Upload .mp4 file → Get format error
- [ ] Refresh during processing → Handle gracefully

**✅ Design/UX**
- [ ] Mobile responsive (test on phone)
- [ ] Buttons work
- [ ] Copy is clear
- [ ] No console errors

---

## Part 11: Cost Reality Check (After MVP)

### If You Scale Beyond 1 User

Render's free tier is fine for solo testing but isn't meant for production traffic (it sleeps when idle and has limited RAM). If you scale up, budget for:

```
At 10-100 users (light traffic):
├─ Render: $7/month (Starter instance — always-on, 512MB RAM)
├─ Vercel: $0 (free tier)
└─ TOTAL: ~$7/month

At 1,000+ users:
├─ Render: $25+/month (higher RAM instance for essentia under load)
├─ Vercel: $20+ (Pro plan)
└─ TOTAL: Revisit architecture at this point — this doc only
   covers the single-user MVP
```

---

## Part 12: Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "404" when calling backend | URL wrong in React code | Check exact Render service URL |
| Slow first request | Render free instance was asleep | Normal on free tier; expect 30-60s delay after idle |
| Build fails on Render | Missing/broken `requirements.txt` | Check build logs in the Render dashboard |
| Python dependencies fail | `essentia` build issues | Render's Python build environment includes standard build tools; if it still fails, check Render's build log for the missing system package |
| Vercel deployment failed | GitHub integration broken | Reconnect Vercel to GitHub |
| CORS errors calling backend | Render service doesn't allow frontend origin | Add CORS middleware in FastAPI allowing your Vercel domain |

---

## Part 13: Next Steps Checklist

### Remaining Setup
- [ ] Create Render account & web service (root: `backend`)
- [ ] Add Spotify secrets to Render environment
- [ ] Confirm Vercel root directory is `frontend`
- [ ] Install Node.js, Python locally

### Week 1 (Bootstrap Phase)
- [ ] Clone repo locally
- [ ] Create React app with Vite in `frontend/`
- [ ] Install Tailwind, dependencies
- [ ] Push to GitHub → Vercel auto-deploys
- [ ] Build first components (Button, UploadZone)

### Week 2-3 (Core Development)
- [ ] Build FastAPI app in `backend/`
- [ ] Push to GitHub → Render auto-deploys
- [ ] Connect frontend to backend
- [ ] Test end-to-end with real MP3
- [ ] Iterate on UI/UX

### Week 4 (Testing & Refinement)
- [ ] Full testing (functionality, responsive, accessibility)
- [ ] Bug fixes
- [ ] Performance optimization
- [ ] Document setup & deployment

---

## Part 14: Tech Stack Summary (CONFIRMED ✅)

### Final Stack Agreement:

**Frontend:**
- ✅ React 18 + TypeScript
- ✅ Vite (build tool)
- ✅ Tailwind CSS (styling)
- ✅ Vercel (hosting)

**Backend:**
- ✅ Python 3.11
- ✅ Render (native Python web service, no Docker)
- ✅ librosa (BPM detection)
- ✅ essentia (key detection)
- ✅ Spotify API (genre - optional)
- ✅ mutagen (ID3 tags)

**Storage:**
- ✅ None — files are never persisted; processed synchronously per request
- ✅ No database for Phase 1

**Deployment:**
- ✅ GitHub (version control) — `a-popa-apps/music-app`
- ✅ Vercel (frontend auto-deploy)
- ✅ Render (backend auto-deploy on push)

**Cost:**
- ✅ $0/month for single user MVP, no credit card required
- ✅ Revisit hosting choice if you scale past a handful of users

---

## QUICK START: Copy-Paste Commands

```bash
# 1. Clone the repo (already created on GitHub)
git clone https://github.com/a-popa-apps/music-app.git
cd music-app

# 2. Create React frontend
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install tailwindcss postcss autoprefixer react-dropzone axios
npx tailwindcss init -p
cd ..

# 3. Create Python backend folder structure
mkdir -p backend/app
cd backend

# 4. Create requirements.txt
cat > requirements.txt << EOF
librosa==0.10.0
essentia==2.1b6.dev1177
mutagen==1.46.0
spotipy==2.23.0
pydub==0.25.1
soundfile==0.12.1
fastapi==0.110.0
uvicorn==0.29.0
python-multipart==0.0.9
EOF

# 5. Push to GitHub
cd ..
git add .
git commit -m "Initial commit: Quickie MVP"
git push -u origin main

# 6. Deploy frontend (Vercel handles this automatically after GitHub push)
# 7. Deploy backend (create the Render Web Service via the dashboard, see Part 4)
```

---

## 🎉 Almost Ready!

**Three of four required services are set up. Just need Render for the backend.**

Next: I can help you write the first React component or the FastAPI backend. Which would you like to start with?

---

## FINAL CHECKLIST (Before You Start Coding)

- [x] GitHub account created & repo initialized (`a-popa-apps/music-app`)
- [ ] Vercel connected to GitHub, root directory set to `frontend`
- [ ] Render account created & web service created (root directory `backend`)
- [x] Spotify developer app created (optional)
- [ ] Node.js installed (v18+)
- [ ] Python 3.11 installed (for local dev, optional)
- [x] You understand the tech stack
- [x] You know the cost is $0/month for MVP, no card required

**Almost ready to build!**
