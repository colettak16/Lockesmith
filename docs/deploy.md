# Deploying Lockesmith to Cloud Run (continuous deploy from GitHub)

This follows the course guide, [Deploying to Cloud Run from GitHub](https://docs.google.com/document/d/1GZHWyRmOGXGJqsiIPMypKUZFRVTReCDJgC_8AdekaXk/edit), which assumes [Setting up GCP and Gemini](https://docs.google.com/document/d/1DSdDGTEt_TAGqL3HLwRB5bkCmul_cgIf0z9xweDvUkg/edit) is done. Where the two differ, the course guide wins; the notes below only add what's specific to this repo.

Cloud Build builds the repo with Google's Python buildpack, as the course guide does. It picks uv because `uv.lock` sits next to `pyproject.toml`, installs the locked runtime dependencies, and uses the Python version in `.python-version` (3.13; the current Ubuntu 24.04 builder offers 3.13 and newer only, so a 3.12 pin fails the build). Keep `uv.lock` committed and current (`uv lock` after editing `pyproject.toml`), and don't add a `requirements.txt`: the buildpack would use it instead of the lockfile. Cloud Run injects `PORT`; the entrypoint binds to it. Nothing here needs a local Docker install.

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
   - Build type: **Go, Node.js, Python, Java, .NET Core, Ruby or PHP via Google Cloud's buildpacks**
   - Build context directory: leave blank (repo root)
   - Entrypoint: `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - Function target: leave blank
   - Click **Save**
4. **Authentication:** **Require authentication**, keep **IAM** checked, and check **Identity-Aware Proxy (IAP)**. Click **Edit policy** and set Principal 1 to `columbia.edu` (it won't autocomplete). Columbia's org policy blocks **Allow public access**, so this is the only option; graders sign in with their Columbia accounts.
5. **Service settings:**
   - Service name: `lockesmith`
   - Region: `us-east4` (what the live service uses; `us-east1` is also fine)
   - Billing: **Request-based**
   - Minimum instances: `0` for now. Bump to `1` during the grading window to avoid cold starts.
   - Maximum instances: `3` (caps spend if something loops)
6. Expand **Container(s), Volumes, Networking, Security**:
   - Container port: `8080`
   - Memory: `1 GiB`, CPU: `1`
   - **Request timeout: `600` seconds** (graders wait up to 5 min; our request budget is ~120 s)
   - Concurrency: `20`
   - Execution environment: **Second generation** (full Linux compatibility and faster CPU for DuckDB; needs at least 512 MiB)
   - Ingress: **All**. IAP still does the sign-in; **Internal** would block graders' browsers.
   - Variables & Secrets: none needed for hello-world. Phase 2 adds model env vars (see below).
7. **Create.** The first build takes a few minutes. When it's green, click the service name for its URL and check in a browser signed in to your Columbia account (IAP turns away `curl` without a token):
   - `/` shows the Lockesmith page
   - `/health` returns `{"status": "ok", "revision": "lockesmith-000xx-..."}` (Cloud Run reserves paths ending in `z`, so `/healthz` gets Google's own 404)
   - `/chat`: on the `/` page, open the browser console and run
     `fetch('/chat', {method: 'POST', headers: {'content-type': 'application/json'}, body: JSON.stringify({message: 'hi'})}).then(r => r.json()).then(console.log)`
     and check you get the `{response, session_id, tool_calls, ...}` shape

From then on, every push to `main` builds and rolls out a new revision.

## After it works

- Put the URL in `submission.json` (`deploy_url`).
- `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_HOST` as secrets in Phase 4.

## Turning on the agent (Phase 2)

`/chat` calls Gemini on Vertex AI. The deployed service needs three things in the console:

1. **Let the service call Vertex AI.** Go to IAM & Admin → IAM → **Grant access**. Set the principal to the service's runtime account, `816944548222-compute@developer.gserviceaccount.com` (or the one shown under the service's Security tab). Give it the role **Vertex AI User** (`roles/aiplatform.user`). No API key is involved.
2. **Turn on session affinity.** Go to Cloud Run → `lockesmith` → **Edit & deploy new revision** → Networking (or the Container tab, depending on the console version) → check **Session affinity**. Conversations, learned rules and rejected picks live in one instance's memory, so follow-up messages must reach the same instance.
3. **Environment variables** (optional; the defaults are below). Set them on the same Edit screen, under Variables & Secrets:
   - `VERTEXAI_PROJECT` (default `lockesmith`) and `VERTEXAI_LOCATION` (default `global`; the current Gemini models answer only on `global`, and `us-east4` returns 404).
   - `LOCKESMITH_FAST_MODEL` (default `vertex_ai/gemini-3.5-flash`): the Clarifier, researchers and Writer.
   - `LOCKESMITH_STRONG_MODEL` (default `vertex_ai/gemini-3.1-pro-preview`): the Lead.
   - `LOCKESMITH_FALLBACK_MODEL` (default `vertex_ai/gemini-3.8-flash`): takes over a call that was rate-limited (429).

   To switch to Claude, set these to a LiteLLM Claude model string. On Vertex, Claude needs enabling in Model Garden first; with an Anthropic API key, store `ANTHROPIC_API_KEY` in Secret Manager and reference it here.

Deploy, then ask the deployed `/chat` something real (the browser-console `fetch` from step 7 above). A full catch plan takes about 50 seconds; clarifying questions come back in about 2. Locally, `gcloud auth application-default login` covers the same calls, and `uv run python scripts/phase2_acceptance.py` runs the acceptance scenarios.
- Private repo: add `codeboi07`, `bhuvighosh3`, `nniishhh`, `x` as collaborators (Settings → Collaborators).

## Checking a failed deploy

- First build fails with `Permission 'developerconnect.gitRepositoryLinks.fetchReadToken' denied`: the new Developer Connect link was still being provisioned. Wait a minute, then Cloud Build → History → the failed build → **Rebuild**.
- Build missing from Cloud Build → History: check the region selector at the top. Builds run in the Developer Connect connection's region, which may not be the service's region.
- Cloud Build → History shows the build log (dependency errors, or a stale `uv.lock`).
- Cloud Run → service → Logs shows startup errors. The usual one is the app not listening on `$PORT`: check the entrypoint matches step 3 exactly.
