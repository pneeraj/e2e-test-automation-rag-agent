# Official Playwright image: browsers + all OS deps pre-installed.
# Tag must match the @playwright/test version in package.json - a mismatch
# means "browser not found" at runtime.
FROM mcr.microsoft.com/playwright:v1.62.1-jammy

# Python for the ci/ orchestrator scripts and the RAG defect agent
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Layer-cache dependencies: these two steps only re-run when the lockfile
# or requirements change, not on every source edit.
COPY package.json package-lock.json ./
RUN npm ci

COPY rag-defect-agent/requirements.txt rag-defect-agent/
RUN pip3 install --no-cache-dir -r rag-defect-agent/requirements.txt

COPY . .

# Default: run every suite. Jenkins overrides the command per stage.
CMD ["python3", "ci/run_tests.py", "--suite", "all"]
