# Contributing to alenabraham.me

Thank you for your interest in contributing to my personal website! This document outlines the workflow and best practices to follow when making changes.

## Development Workflow

### Branch Strategy

We follow a feature branch workflow:

1. **Main Branches**:
   - `hugo`: The main production branch that deploys to alenabraham.me
   - `develop`: (Future) Pre-production branch that will deploy to preprod.alenabraham.me

2. **Feature Branches**:
   - Create a feature branch for each new feature or fix
   - Follow the naming convention:
     - `feature/descriptive-name` for new features
     - `fix/descriptive-name` for bug fixes
     - `content/descriptive-name` for content updates

### Pull Request Process

1. **Create a PR**:
   - Make changes in your feature branch
   - Test locally using `hugo server`
   - Push your branch to the fork repository
   - Create a PR to the appropriate target branch

2. **PR Review**:
   - All PRs must be reviewed before merging
   - Address any feedback or comments

3. **Merging**:
   - After approval, merge the PR
   - Delete the feature branch after merging

### Fork Sync Process

If you're working from a fork:

1. **Set up upstream**:
   ```
   git remote add upstream https://github.com/abrahamalen/alen-abraham.github.io.git
   ```

2. **Keep your fork in sync**:
   ```
   git fetch upstream
   git checkout hugo
   git merge upstream/hugo
   git push origin hugo
   ```

## Code Standards

### HTML/Template Standards

- Indent using 2 spaces
- Keep template logic simple and readable
- Comment complex template logic
- Follow Hugo's best practices for partials and layouts

### Content Standards

- Use clear, descriptive titles for posts
- Include appropriate front matter for all content
- Proofread content before submitting
- Optimize images before adding them to the repository

## Commit Message Guidelines

Follow the conventional commits format:

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools

Example: `fix: Correct time display in about page` 