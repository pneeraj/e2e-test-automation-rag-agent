# Jenkins CI Setup

How the `e2e-playwright` pipeline is wired on a local Windows machine, from a bare
`jenkins.war` to a passing parameterized build. Written for this repo, but the steps apply
to any Windows box without admin rights or Docker.

## 1. Prerequisites

| Requirement | Why | This setup |
|---|---|---|
| Java 21+ | Jenkins LTS (2.5xx+) refuses to start on Java 17 | Portable Temurin JDK 21 ZIP extracted to `%USERPROFILE%\jdk21` - no installer, no admin |
| Node.js + npm | Playwright suites | Already on PATH |
| Python 3 (`py` launcher) | `ci/` scripts + RAG agent | **Note:** on this machine `python.exe` is blocked by group policy - always use `py` |
| Git | Jenkins checks the repo out per build | Already on PATH |

Docker is deliberately **not** used - Docker Desktop is blocked by IT policy here. The
[Dockerfile](../Dockerfile) in the repo targets Linux CI agents and is not needed locally.

## 2. Starting Jenkins

Jenkins runs from the WAR (not as a Windows service), so it lives only as long as its
terminal:

```powershell
& "$env:USERPROFILE\jdk21\jdk-21.0.12.1+1\bin\java.exe" `
    "-Djavax.net.ssl.trustStoreType=WINDOWS-ROOT" `
    -jar "$env:USERPROFILE\OneDrive - Stellantis\Documents\jenkins.war" --httpPort=8080
```

Two flags matter:

- **`-Djavax.net.ssl.trustStoreType=WINDOWS-ROOT`** - corporate networks do TLS
  inspection; without this, Jenkins can't reach its plugin update site (`PKIX path
  building failed`). This flag makes Java trust the Windows certificate store, which
  already contains the company root CA.
- **`--httpPort=8080`** - UI at http://localhost:8080. Jenkins data lives in
  `C:\Users\<you>\.jenkins`.

## 3. One-time Jenkins configuration

1. Unlock with the password from `~\.jenkins\secrets\initialAdminPassword`, install
   **suggested plugins**, create your admin user.
2. Install one extra plugin: **HTML Publisher** (the pipeline's `publishHTML` step).
3. Add two **Secret text** credentials (Manage Jenkins → Credentials → Global):

   | ID | Used for |
   |---|---|
   | `jira-api-token` | RAG agent filing defects in Jira |
   | `openai-api-key` | RAG agent's LLM calls |

   Placeholder values are fine until you want real triage - the pipeline runs with
   `RAG_DRY_RUN=true` by default, which prints draft tickets instead of filing them.
4. Because this job checks out from a **local path** (`file:///D:/endtoendplaywright`),
   the git plugin needs its safety latch released. Script console
   (Manage Jenkins → Script Console):

   ```groovy
   hudson.plugins.git.GitSCM.ALLOW_LOCAL_CHECKOUT = true
   ```

   This resets on restart. Not needed at all once the job points at a real remote
   (GitHub/GitLab) instead of a local directory.

## 4. Creating the job - no UI clicking

The job is provisioned as code by [create_jenkins_job.py](create_jenkins_job.py):

```powershell
$env:JENKINS_USER = 'your-user'
$env:JENKINS_TOKEN = 'your-api-token'   # Jenkins avatar -> Security -> API Token
py ci/create_jenkins_job.py                        # create or update the job
py ci/create_jenkins_job.py --trigger --suite api  # ...and start a build
```

The script is idempotent - re-running it overwrites the job config, so this file (not the
Jenkins UI) is the source of truth. It talks to the REST API with CSRF-crumb auth and
declares the job's parameters up front so `--trigger` works even on the very first build.

Useful flags: `--jenkins-url`, `--job-name`, `--repo-url`, `--branch`.

## 5. Build parameters

| Parameter | Default | Purpose |
|---|---|---|
| `SUITE` | `all` | Run everything or just `ui` / `api` / `mobile` - other suite stages are skipped via `when` conditions |
| `SAUCE_BASE_URL` | https://www.saucedemo.com | UI target - point at another environment without touching code |
| `BOOKING_API_BASE_URL` | https://restful-booker.herokuapp.com | API target |
| `RUN_TRIAGE` | `true` | Skip the RAG defect-triage stage entirely when `false` |

The URL parameters flow through the pipeline `environment {}` block into
[src/utils/env.ts](../src/utils/env.ts), which is the single place tests read config from.

## 6. Pipeline stages

```
Checkout -> Install -> UI tests -> API tests -> Mobile tests -> Summarize -> Triage failures
                                                                    |
                                            post: archive + publish HTML report (always)
```

- **Install** - `npm ci`, `npx playwright install chromium webkit`, `py -m pip install -r rag-defect-agent/requirements.txt`
- **Suite stages** - each calls `py ci\run_tests.py --suite <name>`; they run sequentially
  because parallel Playwright runs on a single box fight over CPU and the report folder
- **Summarize** - `py ci\summarize_report.py` converts Playwright's JSON report into
  `test-results/failures.json` and prints a pass/fail table; its non-zero exit on failures
  is swallowed (`returnStatus: true`) so reporting still happens
- **Triage failures** - only runs when `failures.json` exists *and* `RUN_TRIAGE` is true;
  hands each failure to the LangChain RAG agent which drafts (or files) a Jira defect
- **Post** - Playwright HTML report is archived and published on every build, pass or fail

## 7. Troubleshooting log (issues actually hit, in order)

| Symptom | Root cause | Fix |
|---|---|---|
| Jenkins exits at startup: "older than the minimum required version (Java 21)" | System Java is 17 | Portable JDK 21 ZIP, run WAR with its full path |
| `PKIX path building failed` on plugin install | Corporate TLS inspection | `-Djavax.net.ssl.trustStoreType=WINDOWS-ROOT` |
| Checkout aborted: "references a local directory, which may be insecure" | git plugin blocks `file://` remotes | Script console: set `GitSCM.ALLOW_LOCAL_CHECKOUT = true` (the `-D` system property alone does **not** work - the field is read at class load) |
| pip compiles numpy from source, fails with "Unknown compiler(s)" | Hard-pinned old langchain/chromadb forced `numpy<2`, which has no Python 3.13 wheel | Relaxed [requirements.txt](../rag-defect-agent/requirements.txt) to version ranges |
| `python` not recognized / blocked | Group policy blocks `python.exe` | Pipeline and docs use the `py` launcher everywhere |
| `publishHTML ... directory does not exist` on failed builds | Suites never ran, so no report was generated | Expected side effect of an Install failure; fixed by the numpy fix above |

## 8. Verified result

- Build **#5** - full run (`SUITE=all`): UI 6, API 3, mobile 4 tests - **SUCCESS**
- Build **#6** - `SUITE=api`: UI/mobile stages skipped by `when`, 3 API tests passed - **SUCCESS**
