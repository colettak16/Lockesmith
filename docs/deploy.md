# Deploying Lockesmith to Cloud Run (continuous deploy from GitHub)

This follows the course guide, [Deploying to Cloud Run from GitHub](https://docs.google.com/document/d/1GZHWyRmOGXGJqsiIPMypKUZFRVTReCDJgC_8AdekaXk/edit), which assumes [Setting up GCP and Gemini](https://docs.google.com/document/d/1DSdDGTEt_TAGqL3HLwRB5bkCmul_cgIf0z9xweDvUkg/edit) is done. Where the two differ, the course guide wins; the notes below only add what's specific to this repo.

The repo builds from the root `Dockerfile` (Python 3.12 + uv, dependencies locked by `uv.lock`). Cloud Run injects `PORT`; the container listens on it. Nothing here needs a local Docker install: Cloud Build does the build.

Console labels shift a little between GCP releases. If a label below doesn't match exactly, the step order still applies.

## One-time setup

1. **Project and billing.** Use the project from "Setting up GCP and Gemini": created under your Columbia account, linked to "Billing Account for Education".
2. **Enable APIs.** **Agent Platform API** (`aiplatform.googleapis.com`, formerly Vertex AI; Phase 2 calls Gemini through it) and **Secret Manager API** (Developer Connect keeps its GitHub credentials there). The console enables Cloud Run, Cloud Build and Artifact Registry itself when you create the service. If the console offers **Create credentials** after enabling an API, cancel it: nothing here uses API keys, OAuth clients or service account key files.
3. **Push the repo to GitHub.** `main` is the deploy branch.

## Create the service

1. Cloud Run → **Connect repository** → **Continuous deploy from a repository** → **Developer Connect** → **Set up with Developer Connect**.
2. **Repository:** drop-down → **Link new repository** → GitHub → Continue → "I understand and continue". Install the Developer Connect GitHub app on your account with access to the `Lockesmith` repo only, then pick the repo from the drop-down.
3. **Build configuration:**
   - Branch: `^main$`
   - Build type: **Dockerfile**, source location `/Dockerfile`. (The course guide uses a buildpack with entrypoint `uvicorn app:app --host 0.0.0.0 --port $PORT`; that also works for this repo and is the fallback if the Dockerfile build fails.)
4. **Authentication:** **Require authentication**, keep **IAM** checked, and check **Identity-Aware Proxy (IAP)**. Click **Edit policy** and set Principal 1 to `columbia.edu` (it won't autocomplete). Columbia's org policy blocks **Allow public access**, so this is the only option; graders sign in with their Columbia accounts.
5. **Service settings:**
   - Service name: `lockesmith`
   - Region: `us-east1` (closest low-cost region to NYC; `us-east4` also fine)
   - Billing: **Request-based**
   - Minimum instances: `0` for now. Bump to `1` during the grading window to avoid cold starts.
   - Maximum instances: `3` (caps spend if something loops)
6. Expand **Container(s), Volumes, Networking, Security**:
   - Container port: `8080`
   - Memory: `1 GiB`, CPU: `1`
   - **Request timeout: `600` seconds** (graders wait up to 5 min; our request budget is ~120 s)
   - Concurrency: `20`
   - Variables & Secrets: none needed for hello-world. Phase 2 adds model env vars (see below).
7. **Create.** The first build takes a few minutes. When it's green, click the service name for its URL and check in a browser signed in to your Columbia account (IAP turns away `curl` without a token):
   - `/` shows the Lockesmith page
   - `/healthz` returns `{"status": "ok", "revision": "lockesmith-000xx-..."}`
   - `/chat`: on the `/` page, open the browser console and run
     `fetch('/chat', {method: 'POST', headers: {'content-type': 'application/json'}, body: JSON.stringify({message: 'hi'})}).then(r => r.json()).then(console.log)`
     and check you get the `{response, session_id, tool_calls, ...}` shape

From then on, every push to `main` builds and rolls out a new revision.

## After it works

- Put the URL in `submission.json` (`deploy_url`).
- Phase 2 env vars (Service → Edit & deploy new revision → Variables & Secrets). Names are placeholders until the runtime lands:
  - `LOCKESMITH_LEAD_MODEL`, `LOCKESMITH_RESEARCHER_MODEL` (model strings)
  - `VERTEXAI_PROJECT=<project id>`, `VERTEXAI_LOCATION=us-east1` (or `global`), and grant the service's runtime service account the **Vertex AI User** role (`roles/aiplatform.user`; IAM → the `...-compute@developer.gserviceaccount.com` account, unless you set a dedicated one). No API key needed. Locally, `gcloud auth application-default login` covers the same calls.
- `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_HOST` as secrets in Phase 4.
- Private repo: add `codeboi07`, `bhuvighosh3`, `nniishhh`, `x` as collaborators (Settings → Collaborators).

## Checking a failed deploy

- First build fails with `Permission 'developerconnect.gitRepositoryLinks.fetchReadToken' denied`: the new Developer Connect link was still being provisioned. Wait a minute, then Cloud Build → History → the failed build → **Rebuild**.
- Build missing from Cloud Build → History: check the region selector at the top. Builds run in the Developer Connect connection's region, which may not be the service's region.
- Cloud Build → History shows the build log (dependency or Dockerfile errors).
- Cloud Run → service → Logs shows startup errors. The usual one is the app not listening on `$PORT`; the Dockerfile's `CMD` handles that.
