---
title: "Web App Deployment"
parent: Reference
nav_order: 4
layout: default
---

# Deployment Guide: Firebase Web Application
{: .no_toc }

Step-by-step instructions for deploying your own instance of the data-collection web application on Firebase.
{: .fs-6 .fw-300 }

## Table of contents
{: .no_toc .text-delta }

1. TOC
{:toc}

---

## Overview

The data collection webapp is built on Firebase and provides a structured flow for the crossover study: participant registration, pre-test, challenge tasks (with or without AI), post-challenge perception surveys, and post-test. This guide explains how to deploy your own instance.

## Prerequisites

- A Google account
- Node.js (version 18 or higher) and npm installed
- Firebase CLI installed globally: `npm install -g firebase-tools`
- Basic familiarity with the command line

You do not need prior experience with Firebase. This guide walks through every step. However, if you plan to customize the webapp beyond configuration changes, familiarity with HTML, CSS, and JavaScript will be helpful.
{: .note }

## Architecture

The webapp consists of:

- **Firebase Hosting**: Serves the static frontend (HTML/CSS/JS)
- **Firebase Authentication**: Manages participant login (anonymous or email-based)
- **Cloud Firestore**: Stores all study data (responses, timestamps, scores)
- **Firebase Security Rules**: Ensures participants can only read/write their own data

## Step-by-Step Deployment

### 1. Create a Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/).
2. Click "Add project" and give it a name (e.g., `crossover-study-2026`).
3. Disable Google Analytics if not needed (simplifies setup).
4. Wait for the project to be created.

### 2. Enable Required Services

In the Firebase Console for your project:

1. **Authentication**: Go to Authentication > Sign-in method. Enable "Anonymous" and optionally "Email/Password".
2. **Firestore**: Go to Cloud Firestore > Create database. Start in **test mode** for development (switch to production rules before data collection).
3. **Hosting**: Go to Hosting > Get started.

Do not collect real participant data while Firestore is in test mode. Test mode allows unrestricted read/write access to your database, meaning anyone with the project ID could access or modify the data.
{: .warning }

### 3. Configure the Webapp

1. In the Firebase Console, go to Project settings > General > Your apps > Web app.
2. Register a new web app and copy the Firebase config object.
3. Place the config in the webapp's configuration file (e.g., `webapp/src/firebase-config.js`):

```javascript
const firebaseConfig = {
  apiKey: "your-api-key",
  authDomain: "your-project.firebaseapp.com",
  projectId: "your-project-id",
  storageBucket: "your-project.appspot.com",
  messagingSenderId: "123456789",
  appId: "your-app-id"
};
```

The `apiKey` in Firebase config is not a secret -- it is used to identify your project on the client side. Access control is enforced by Firestore Security Rules, not by keeping the API key private.
{: .tip }

### 4. Configure Study Parameters

Edit the study configuration file to define:

- Number of periods (default: 2)
- Sequence allocation (AB/BA)
- Challenge task descriptions for each period
- Likert scale items for the perception survey
- Time limits (if any)
- AI tool integration settings (API key, model, prompt constraints)

Unlike the Firebase config, AI API keys (e.g., OpenAI, Anthropic) are secrets and must never be committed to version control or exposed in client-side code. Use environment variables or server-side functions.
{: .warning }

### 5. Set Firestore Security Rules

Replace the default rules with production rules that restrict access:

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /participants/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    match /responses/{docId} {
      allow create: if request.auth != null;
      allow read: if request.auth != null &&
                     resource.data.userId == request.auth.uid;
    }
    match /admin/{docId} {
      allow read, write: if false;  // Admin access via server SDK only
    }
  }
}
```

These rules ensure that each participant can only access their own data. Administrative operations (data export, configuration changes) are performed exclusively through the Firebase Admin SDK on the server side.
{: .note }

### 6. Deploy

```bash
# Login to Firebase
firebase login

# Initialize the project (select Hosting and Firestore)
firebase init

# Deploy
firebase deploy
```

Your app will be available at `https://your-project.web.app`.

### 7. Pre-Study Checklist

Before collecting real data:

- [ ] Test the full participant flow (registration through post-test)
- [ ] Verify that data is saved correctly in Firestore
- [ ] Check that randomization assigns participants to sequences correctly
- [ ] Test on multiple devices and browsers
- [ ] Switch Firestore to production security rules
- [ ] Obtain ethics committee approval
- [ ] Prepare informed consent form (see [Ethical Considerations](ethics))

Complete every item on this checklist before opening the study to real participants. A single missed step (e.g., forgetting to switch to production security rules) can compromise your entire dataset.
{: .warning }

## Data Export

After data collection, export data from Firestore:

1. Use the Firebase Console's export feature, or
2. Run the provided export script: `node webapp/scripts/export_data.js`
3. The export produces a CSV file compatible with the R analysis pipeline

Export your data promptly after the study ends and store a backup copy in a secure location. Do not rely on Firebase as your only data repository.
{: .tip }

## Troubleshooting

| Issue | Solution |
|:------|:---------|
| Authentication errors | Check that the sign-in method is enabled in Firebase Console |
| Data not saving | Verify Firestore rules allow writes for authenticated users |
| Deployment fails | Run `firebase login --reauth` and try again |
| CORS errors | Ensure the webapp domain is authorized in Firebase Authentication settings |

## Cost Considerations

For a typical study (100--300 participants), Firebase's free tier (Spark plan) is usually sufficient:
- Firestore: 50K reads/day, 20K writes/day
- Hosting: 10 GB/month transfer
- Authentication: Unlimited for most providers

If your study involves frequent AI API calls routed through Cloud Functions, those costs are separate and depend on the AI provider's pricing. Budget for API costs before the study begins.
{: .note }
