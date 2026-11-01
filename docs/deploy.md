# Deploying Lockesmith to Cloud Run (continuous deploy from GitHub)

The repo builds from the root `Dockerfile` (Python 3.12 + uv, dependencies locked by `uv.lock`). Cloud Run injects `PORT`; the container listens on it. Nothing here needs a local Docker or `gcloud` install: Cloud Build does the build.

Console labels shift a little between GCP releases. If a label below doesn't match exactly, the step order still applies.

## One-time setup

1. **Project and billing.** In the GCP console, pick (or create) the project you'll use for the course and confirm billing is attached (course credits count).
2. **Enable APIs.** APIs & Services → Enable APIs: **Cloud Run Admin API**, **Cloud Build API**, **Artifact Registry API**. If we go with Vertex AI for models (see `docs/decisions.md`, D3), also enable **Vertex AI API** now.
3. **Push the repo to GitHub.** `main` is the deploy branch.

## Create the service

1. Cloud Run → **Deploy container** → **Service**.
2. Choose **Continuously deploy from a repository (source or function)** → **Set up with Cloud Build**.
3. **Repository provider:** GitHub. Authenticate, install the Cloud Build GitHub app on your account, and grant it access to the `Lockesmith` repo only. Select the repo.
4. **Build configuration:**
   - Branch: `^main$`
   - Build type: **Dockerfile**
   - Source location: `/Dockerfile`
5. **Service settings:**
   - Service name: `lockesmith`
   - Region: `us-east1` (closest low-cost region to NYC; `us-east4` also fine)
   - Authentication: **Allow unauthenticated invocations** (graders hit it from a browser)
   - Billing: **Request-based**
   - Minimum instances: `0` for now. Bump to `1` during the grading window to avoid cold starts.
   - Maximum instances: `3` (caps spend if something loops)
6. Expand **Container(s), Volumes, Networking, Security**:
   - Container port: `8080`
   - Memory: `1 GiB`, CPU: `1`
   - **Request timeout: `600` seconds** (graders wait up to 5 min; our request budget is ~120 s)
   - Concurrency: `20`
   - Variables & Secrets: none needed for hello-world. Phase 2 adds model env vars (see below).
7. **Create.** The first build takes a few minutes. When it's green, open the service URL and check:
   - `GET /` shows the Lockesmith page
   - `GET /healthz` returns `{"status": "ok", "revision": "lockesmith-000xx-..."}`
   - `curl -X POST <url>/chat -H 'content-type: application/json' -d '{"message":"hi"}'` returns the `{response, session_id, tool_calls, ...}` shape

From then on, every push to `main` builds and rolls out a new revision.

## After it works

- Put the URL in `submission.json` (`deploy_url`).
- Phase 2 env vars (Service → Edit & deploy new revision → Variables & Secrets). Names are placeholders until the runtime lands:
  - `LOCKESMITH_LEAD_MODEL`, `LOCKESMITH_RESEARCHER_MODEL` (LiteLLM model strings)
  - Vertex route: `VERTEXAI_PROJECT=<project id>`, `VERTEXAI_LOCATION=us-east1` (or `global`), and grant the service's runtime service account the **Vertex AI User** role (IAM → the `...-compute@developer.gserviceaccount.com` account, unless you set a dedicated one). No API key needed.
  - Anthropic route instead: store the key in **Secret Manager** and expose it as `ANTHROPIC_API_KEY` (Variables & Secrets → Reference a secret). Never put it in the repo.
- `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_HOST` as secrets in Phase 4.
- Private repo: add `codeboi07`, `bhuvighosh3`, `nniishhh`, `x` as collaborators (Settings → Collaborators).

## Checking a failed deploy

- Cloud Build → History shows the build log (dependency or Dockerfile errors).
- Cloud Run → service → Logs shows startup errors. The usual one is the app not listening on `$PORT`; the Dockerfile's `CMD` handles that.
