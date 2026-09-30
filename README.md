# GST ITC Invoice Exception Agent

A safe ADK starter agent for resolving invoice/GST matching exceptions. It uses
local, read-only fixture tools for three demo cases:

- `INV-1001`: normal match, suitable for approval recommendation.
- `INV-1002`: variance exceeds the ₹500 threshold; escalate.
- `INV-1003`: invoice GSTIN differs from vendor record; escalate.

## Run locally

Install Python 3.10 or newer, then in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item gst_invoice_exception_agent\.env.example gst_invoice_exception_agent\.env
# Edit .env with your Google Cloud development project. Keep the local model
# endpoint as `global`; choose your deployment region separately.
gcloud auth application-default login
adk web
```

Select `gst_invoice_exception_agent` in the ADK web UI and ask:

```text
Investigate invoice INV-1001.
```

The starter deliberately has no write tool. Connect real ERP/GST systems using
read-only service-account credentials before enabling a separately reviewed,
human-approved write action.

## Cloud Run deployment

The `cloudbuild.yaml` file builds this container, stores it in Artifact
Registry, and deploys it to a Cloud Run service. The deployed
service listens on Cloud Run's `PORT` and uses its dedicated runtime service
account to call Vertex AI. For a public training demo, the service can grant
the Cloud Run Invoker role to `allUsers`; restrict it again or put it behind
IAP, API Gateway, or another approved authentication layer before production.
