---
title: "What is Github Actions? How does it simplify CI/CD?"
date: 2022-04-08T12:56:25+05:30
weight: 160
draft: false
summary: "A description of github actions - another ci/cd tool."
#tags: ["resources", "ui/ux"]
categories: ["devops"]
aliases: [/devops]
featuredImage: "/images/what-is-github-actions/cover-image.png"
---  

## Github Actions 

**Github Actions** is a Continuous Integration and Continuous Development(CI/CD) platform that allows you to automate your build, test, and deployment pipeline. You can create workflows that build and test every pull request to your repository, or deploy merged pull requests to production.

GitHub Actions goes beyond just DevOps and lets you run workflows when other events happen in your repository.   
For example, you can run a workflow to automatically add the appropriate labels whenever someone creates a new issue in your repository.

- GitHub Actions makes it easy to automate all your software workflows, with CI/CD. 
  - Build, test, and deploy your code right from GitHub. 
  - Make code reviews, branch management, and issue triaging work the way you want.  

- Workflow is triggered by an event.
  - Workflow contains jobs which can have multiple steps - Each step can be associated with an action or a script.  

- Code - defined workflow - 
  - A workflow can contain actions created by the community, or you can create your own actions directly with your application's repository.  

- Support for Python, Java, Node.js, Ruby, PHP, Go, Rust, .NET apps.  

- Great starting point for smaller projects.

- Deploy to cloud.  

I have added a github actions workflow in my personal website repository to automate random changes and commits and run the workflow to deploy the changes successfully. You can checkout the repository [here](https://github.com/abrahamalen/alen-abraham.github.io).  

Thank you for the read.  
Repost on [Hashnode](https://alenabraham.hashnode.dev/what-is-github-actions-how-does-it-simplify-cicd) & [Dev](https://dev.to/alenabraham/what-is-github-actions-how-does-it-simplify-cicd-49m0) 