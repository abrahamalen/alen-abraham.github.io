---
title: "Resume"
layout: "single"
url: "/resume/"
description: "Alen Abraham — SRE & DevOps Engineer"
summary: "Professional resume of Alen Abraham"
---

Making systems reliable, deployments boring, and incidents rare.

[alenabraham@hotmail.com](mailto:alenabraham@hotmail.com) · [alenabraham.me](https://alenabraham.me) · [GitHub](https://github.com/abrahamalen) · [LinkedIn](https://linkedin.com/in/alenabraham)

---

### Experience

<div class="linkedin-exp">

  <div class="exp-company">
    <div class="exp-company-header">
      <div class="exp-company-name">Qure.ai</div>
      <div class="exp-company-meta">Medical imaging AI company using deep learning to detect critical findings in X-rays, CT scans, and emergency radiology — deployed across 15+ AWS regions serving hospitals globally.</div>
      <div class="exp-company-meta">Full-time · 3 yrs 7 mos+ · Bengaluru, India</div>
    </div>
    <div class="exp-roles">
      <div class="exp-role">
        <div class="exp-role-dot"></div>
        <div class="exp-role-content">
          <div class="exp-role-title">Senior DevOps Engineer</div>
          <div class="exp-role-date">Apr 2026 – Present</div>
          <ul class="exp-role-desc">
            <li>Reduced Datadog costs from $50K to $30K/month ($240K annual savings) by implementing Flex Logs and optimizing log ingestion pipelines</li>
            <li>Built Jenkins monitoring dashboard on Datadog, giving developers real-time visibility into CI/CD pipeline health and build status</li>
            <li>Building a public service status page (status.qure.ai) with heartbeat monitoring for real-time uptime visibility across all services</li>
            <li>Migrating CPU-intensive CI tasks from Jenkins to GitHub Actions with S3 caching to improve build performance and reduce infrastructure load</li>
            <li>Driving reliability and scalability improvements for qTrack — optimizing performance for production healthcare workloads</li>
          </ul>
        </div>
      </div>
      <div class="exp-role">
        <div class="exp-role-dot"></div>
        <div class="exp-role-content">
          <div class="exp-role-title">Senior Site Reliability Engineer</div>
          <div class="exp-role-date">Apr 2025 – Mar 2026 · 1 yr</div>
          <ul class="exp-role-desc">
            <li>Designed SLO tracking using Turn Around Time (TAT) as the primary SLI, distinguishing bulk uploads from urgent scans to enable data-driven reliability decisions across 15+ regions</li>
            <li>Implemented end-to-end distributed tracing using Datadog APM with custom trace tags, reducing cross-service debugging time across 3 microservices</li>
            <li>Developed custom Datadog metrics pipeline — Series API for dashboards/alerting (low cardinality), Events API for debugging (high cardinality) — cutting observability costs while maintaining full debuggability</li>
            <li>Architected Bazel-based smart build system for 39+ package monorepo with reverse dependency resolution and parallel dispatch via semaphore-based ordering</li>
            <li>Delivered 3-stage deployment pipeline (TEST → PUBLISH → DEPLOY) with CodeDeploy, decoupling application deployments from infrastructure changes</li>
            <li>Owned Jenkinsfiles and CI/CD workflows across 12+ services, standardizing build, test, and release processes using a shared Jenkins library (Hawkeye)</li>
            <li>Engineered self-healing EC2 instances using IMDSv2 failure detection with automatic ASG replacement, reducing recovery time to under 5 minutes with zero manual intervention</li>
            <li>Optimized ASG auto-scaling (CPU 90%/30%, 10-min evaluation, 5-min cooldown) and reduced ALB deregistration from 300s to 30s, accelerating rolling deployments by 10x</li>
            <li>Deployed on-premise medical imaging solutions across 5+ countries including UAE (SEHA visa screening, Burjeel hospital CT/X-ray, MOH UAE) and Vietnam with end-to-end server setup and DICOM modality integration</li>
            <li>Developed "Pulse" — an internal monitoring platform (Django, React, TypeScript, PostgreSQL) providing real-time health dashboards for on-premise services and DICOM gateway infrastructure globally</li>
            <li>Building "Agent-Qurie" — an AI-powered knowledge base portal (LiteLLM, Open-WebUI, Prometheus) enabling vendors to self-serve L1 incident resolution, reducing escalations to the SRE team</li>
          </ul>
        </div>
      </div>
      <div class="exp-role">
        <div class="exp-role-dot"></div>
        <div class="exp-role-content">
          <div class="exp-role-title">Site Reliability Engineer</div>
          <div class="exp-role-date">Mar 2023 – Mar 2025 · 2 yrs</div>
          <ul class="exp-role-desc">
            <li>Created reusable AWS CDK construct library deploying across 15+ production regions (AWS, Huawei Cloud, Alibaba Cloud) with Pydantic-validated configs preventing misconfigurations before production</li>
            <li>Integrated Bandit SAST scanning on every commit with baseline comparison; established split-PR enforcement to prevent cross-service merge conflicts</li>
            <li>Containerized multiple services with Docker and Docker Compose across staging, production, and on-premise environments with environment-specific configurations</li>
            <li>Co-built internal license management platform (Django + React) handling license lifecycle and deployment coordination for cloud and air-gapped hospital environments</li>
            <li>Established per-region p95/p99 TAT dashboards and error rate monitoring, enabling real-time service visibility and SLO-driven deployment decisions</li>
            <li>Authored SRE Knowledge Base with runbooks, incident response procedures, onboarding guides, and operational documentation adopted across the engineering team</li>
            <li>Maintained and operated Fomema — a legacy healthcare client on Alibaba Cloud since 2022, handling ongoing infrastructure management, incident resolution, and platform stability</li>
          </ul>
        </div>
      </div>
      <div class="exp-role">
        <div class="exp-role-dot"></div>
        <div class="exp-role-content">
          <div class="exp-role-title">Technical Operations Engineer</div>
          <div class="exp-role-date">Sep 2022 – Feb 2023 · 6 mos</div>
          <ul class="exp-role-desc">
            <li>Resolved L1-L3 production issues across cloud and on-premise environments — debugging distributed systems, container failures, network misconfigurations, and application-level errors</li>
            <li>Collaborated cross-functionally with backend, frontend, product, QA, and BD teams; provided infrastructure cost analysis for solution pricing and client proposals</li>
            <li>Led incident response across 15+ regions with on-call rotations including weekends; conducted client-facing technical scoping and served as interim TPM for select clients</li>
          </ul>
        </div>
      </div>
    </div>
  </div>

  <div class="exp-company">
    <div class="exp-company-header">
      <div class="exp-company-name">Tata Consultancy Services</div>
      <div class="exp-company-meta">Trivandrum, India</div>
    </div>
    <div class="exp-roles">
      <div class="exp-role">
        <div class="exp-role-dot"></div>
        <div class="exp-role-content">
          <div class="exp-role-title">Assistant System Engineer</div>
          <div class="exp-role-date">Jul 2021 – Sep 2022 · 1 yr 3 mos</div>
          <ul class="exp-role-desc">
            <li>Built Jenkins CI/CD pipelines for Java Spring Boot applications deployed on GCP; volunteered for 24x7 on-call</li>
          </ul>
        </div>
      </div>
    </div>
  </div>

  <div class="exp-company">
    <div class="exp-company-header">
      <div class="exp-company-name">Naas.ai</div>
      <div class="exp-company-meta">Remote</div>
    </div>
    <div class="exp-roles">
      <div class="exp-role">
        <div class="exp-role-dot"></div>
        <div class="exp-role-content">
          <div class="exp-role-title">Open Source Contributor</div>
          <div class="exp-role-date">Dec 2021 – Aug 2022 · 9 mos</div>
          <ul class="exp-role-desc">
            <li>Design consultant; contributing to documentation and DevOps</li>
          </ul>
        </div>
      </div>
    </div>
  </div>

  <div class="exp-company">
    <div class="exp-company-header">
      <div class="exp-company-name">Cognetry Labs</div>
      <div class="exp-company-meta">Trivandrum, India</div>
    </div>
    <div class="exp-roles">
      <div class="exp-role">
        <div class="exp-role-dot"></div>
        <div class="exp-role-content">
          <div class="exp-role-title">Technical Intern</div>
          <div class="exp-role-date">Nov 2020 – Feb 2021 · 4 mos</div>
          <ul class="exp-role-desc">
            <li>Redesigned company website and designed interfaces for a mobile app and admin panel</li>
          </ul>
        </div>
      </div>
    </div>
  </div>

</div>

---

### Skills

<div class="resume-skills">
  <div class="skill-row"><span class="skill-label">SRE & Observability</span><span class="skill-value">SLOs/SLIs, Datadog (APM, Metrics, Tracing), Incident Response, Blameless Postmortems, On-Call</span></div>
  <div class="skill-row"><span class="skill-label">Cloud & Infrastructure</span><span class="skill-value">AWS (EC2, ASG, ALB, RDS, EFS, S3, CodeDeploy), Huawei Cloud, Alibaba Cloud, Viettel Cloud</span></div>
  <div class="skill-row"><span class="skill-label">IaC & Containers</span><span class="skill-value">AWS CDK (Python), CloudFormation, Ansible, Docker, Docker Compose</span></div>
  <div class="skill-row"><span class="skill-label">CI/CD & Automation</span><span class="skill-value">Jenkins, Bazel, GitHub Actions, CodeDeploy, Bandit SAST</span></div>
  <div class="skill-row"><span class="skill-label">Languages & Frameworks</span><span class="skill-value">Python, Java, TypeScript, Django, React, SQL, Bash</span></div>
  <div class="skill-row"><span class="skill-label">Tools</span><span class="skill-value">Git, Teleport, Jira, Postman, Cloudflare, Claude Code, Cursor</span></div>
</div>

---

### Education

<div class="resume-edu">
  <div class="edu-org">College of Engineering Chengannur</div>
  <div class="edu-date">2017 – 2021</div>
  <div class="edu-degree">B.Tech (Hons.) in Electronics and Communication Engineering · CGPA: 8.1/10</div>
</div>

---

### Languages

<div class="resume-langs">English · German · Malayalam</div>
