# Hugo Template Style Guide

This document outlines the coding standards and best practices for Hugo templates in this project.

## Template Formatting

### Whitespace and Indentation

- Use 2 spaces for indentation
- Use whitespace to separate logical sections of code
- Use `{{- -}}` to trim whitespace in templates when appropriate

### Comments

- Use `{{/* Comment */}}` for single-line comments
- For multi-line comments, use:
  ```
  {{/* 
    This is a 
    multi-line comment 
  */}}
  ```
- Document complex template logic with comments

### Template Structure

- Keep templates modular and focused on a single responsibility
- Extract repeated code into partials
- Use consistent naming conventions:
  - `snake_case` for file names
  - `camelCase` for variables

## Hugo Best Practices

### Variables

- Use descriptive variable names
- Prefix partial-specific variables with the partial name to avoid conflicts
- Use the dot context (`.`) explicitly when necessary for clarity

### Conditionals

- Format complex conditionals with proper indentation:
  ```
  {{- if condition -}}
    content
  {{- else if other_condition -}}
    other content
  {{- else -}}
    default content
  {{- end -}}
  ```

### Ranges

- Format range blocks consistently:
  ```
  {{- range .Items -}}
    <div>{{ .Title }}</div>
  {{- end -}}
  ```

### CSS/JS Resources

- Use `resources.Get` and `resources.Fingerprint` for static assets
- Bundle and minify CSS/JS where possible

## Code Organization

### Partial Templates

- Group related partials in subdirectories
- Name partials descriptively based on their function
- Keep partials small and focused

### Layouts

- Use layout inheritance appropriately
- Don't repeat layout code that can be inherited

## Example

```html
{{- /* Header partial for site navigation */ -}}
<header class="site-header">
  <div class="container">
    <nav>
      {{- range .Site.Menus.main -}}
        <a href="{{ .URL | absURL }}" title="{{ .Name }}">
          {{ .Name }}
        </a>
      {{- end -}}
    </nav>
    
    {{- if .Site.Params.enableSearch -}}
      {{- partial "search/search_button.html" . -}}
    {{- end -}}
  </div>
</header>
``` 