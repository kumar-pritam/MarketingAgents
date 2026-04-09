# Google Integrations Setup

This folder contains OAuth clients for connecting to Google services.

## Getting Started

### 1. Create OAuth Credentials in Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to **APIs & Services** > **Credentials**
4. Click **Create Credentials** > **OAuth client ID**
5. Select **Desktop app** as the application type
6. Give it a name (e.g., "Marketing Agents")
7. Download the JSON file

### 2. Configure Credentials

1. Copy the downloaded JSON file to this folder
2. Rename it to `credentials.json`
3. Or use the template:

```bash
cp credentials.json.example credentials.json
# Edit credentials.json with your OAuth client details
```

### 3. Required OAuth Scopes

#### Google Search Console (GSC)
- `https://www.googleapis.com/auth/webmasters.readonly`

#### Google Analytics 4 (GA4)
- `https://www.googleapis.com/auth/analytics.readonly`
- `https://www.googleapis.com/auth/analytics.edit`

### 4. Enable Required APIs

In Google Cloud Console, enable the following APIs:
- **Google Search Console API** - For GSC integration
- **Google Analytics Data API** - For GA4 integration
- **Google Analytics Admin API** - For listing GA4 properties

### 5. Testing the Connection

Start the backend server and navigate to any agent run page. Click "Connect" on the integration card to start the OAuth flow.

## Troubleshooting

### "OAuth credentials not configured"
- Ensure `credentials.json` exists in this folder
- Verify the JSON structure matches the template

### "Failed to complete OAuth"
- Check that you've enabled the required APIs in Google Cloud Console
- Verify the OAuth consent screen is configured
- For production, you may need to publish your OAuth app

### "Google libraries missing"
- Install required packages:
```bash
pip install google-auth-oauthlib google-api-python-client
```

## Security Notes

- Never commit `credentials.json` or `token.json` to version control
- The `credentials.json` file contains your OAuth client secrets
- Token files (`gsc_token.json`, `ga4_token.json`) contain access tokens
- All files are already in `.gitignore` for this project
