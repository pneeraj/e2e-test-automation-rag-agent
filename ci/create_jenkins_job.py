"""
Creates (or updates) the Jenkins pipeline job for this repo straight from the
command line - no clicking through the Jenkins UI. Safe to re-run: if the job
already exists its config is overwritten, so this file is the single source
of truth for how the job is wired.

Parameter definitions live in the Jenkinsfile's `parameters {}` block; they're
also declared here in the job config so `--trigger` can pass values on the
very first build (before Jenkins has parsed the Jenkinsfile once).

Usage:
    set JENKINS_USER=you
    set JENKINS_TOKEN=your-password-or-api-token
    py ci/create_jenkins_job.py                       # create/update the job
    py ci/create_jenkins_job.py --trigger --suite api # ...and start a build
"""
import argparse
import os
import sys
from pathlib import Path
from xml.sax.saxutils import escape

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent

JOB_CONFIG_TEMPLATE = """<?xml version="1.1" encoding="UTF-8"?>
<flow-definition plugin="workflow-job">
  <description>UI/API/mobile Playwright suites + RAG defect triage. Managed by ci/create_jenkins_job.py - do not edit in the UI.</description>
  <properties>
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <hudson.model.ChoiceParameterDefinition>
          <name>SUITE</name>
          <description>Which test suite to run</description>
          <choices class="java.util.Arrays$ArrayList">
            <a class="string-array">
              <string>all</string>
              <string>ui</string>
              <string>api</string>
              <string>mobile</string>
            </a>
          </choices>
        </hudson.model.ChoiceParameterDefinition>
        <hudson.model.StringParameterDefinition>
          <name>SAUCE_BASE_URL</name>
          <defaultValue>https://www.saucedemo.com</defaultValue>
          <description>UI target</description>
        </hudson.model.StringParameterDefinition>
        <hudson.model.StringParameterDefinition>
          <name>BOOKING_API_BASE_URL</name>
          <defaultValue>https://restful-booker.herokuapp.com</defaultValue>
          <description>API target</description>
        </hudson.model.StringParameterDefinition>
        <hudson.model.BooleanParameterDefinition>
          <name>RUN_TRIAGE</name>
          <defaultValue>true</defaultValue>
          <description>Run the RAG defect-triage agent on failures</description>
        </hudson.model.BooleanParameterDefinition>
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
  </properties>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition" plugin="workflow-cps">
    <scm class="hudson.plugins.git.GitSCM" plugin="git">
      <configVersion>2</configVersion>
      <userRemoteConfigs>
        <hudson.plugins.git.UserRemoteConfig>
          <url>{repo_url}</url>
        </hudson.plugins.git.UserRemoteConfig>
      </userRemoteConfigs>
      <branches>
        <hudson.plugins.git.BranchSpec>
          <name>*/{branch}</name>
        </hudson.plugins.git.BranchSpec>
      </branches>
      <doGenerateSubmoduleConfigurations>false</doGenerateSubmoduleConfigurations>
      <submoduleCfg class="empty-list"/>
      <extensions/>
    </scm>
    <scriptPath>Jenkinsfile</scriptPath>
    <lightweight>true</lightweight>
  </definition>
  <disabled>false</disabled>
</flow-definition>
"""


def make_session(base_url: str, user: str, token: str) -> requests.Session:
    session = requests.Session()
    session.auth = (user, token)
    crumb = session.get(f"{base_url}/crumbIssuer/api/json", timeout=15)
    crumb.raise_for_status()
    data = crumb.json()
    session.headers[data["crumbRequestField"]] = data["crumb"]
    return session


def job_exists(session: requests.Session, base_url: str, job: str) -> bool:
    return session.get(f"{base_url}/job/{job}/api/json", timeout=15).status_code == 200


def create_or_update(session: requests.Session, base_url: str, job: str, config: str) -> str:
    headers = {"Content-Type": "application/xml"}
    if job_exists(session, base_url, job):
        url = f"{base_url}/job/{job}/config.xml"
        action = "updated"
    else:
        url = f"{base_url}/createItem?name={job}"
        action = "created"
    response = session.post(url, data=config.encode("utf-8"), headers=headers, timeout=30)
    response.raise_for_status()
    return action


def trigger(session: requests.Session, base_url: str, job: str, params: dict) -> None:
    response = session.post(f"{base_url}/job/{job}/buildWithParameters", params=params, timeout=15)
    response.raise_for_status()


def main() -> int:
    parser = argparse.ArgumentParser(description="Provision the Jenkins pipeline job for this repo.")
    parser.add_argument("--jenkins-url", default=os.environ.get("JENKINS_URL", "http://localhost:8080"))
    parser.add_argument("--job-name", default="e2e-playwright")
    parser.add_argument("--repo-url", default=f"file:///{REPO_ROOT.as_posix()}")
    parser.add_argument("--branch", default="master")
    parser.add_argument("--trigger", action="store_true", help="Start a build after provisioning")
    parser.add_argument("--suite", default="all", choices=["all", "ui", "api", "mobile"])
    args = parser.parse_args()

    user = os.environ.get("JENKINS_USER")
    token = os.environ.get("JENKINS_TOKEN")
    if not user or not token:
        print("Set JENKINS_USER and JENKINS_TOKEN environment variables first.", file=sys.stderr)
        return 1

    base_url = args.jenkins_url.rstrip("/")
    config = JOB_CONFIG_TEMPLATE.format(repo_url=escape(args.repo_url), branch=escape(args.branch))

    session = make_session(base_url, user, token)
    action = create_or_update(session, base_url, args.job_name, config)
    print(f"Job '{args.job_name}' {action}: {base_url}/job/{args.job_name}/")

    if args.trigger:
        trigger(session, base_url, args.job_name, {"SUITE": args.suite})
        print(f"Build triggered with SUITE={args.suite}")

    return 0


if __name__ == "__main__":
    main()
