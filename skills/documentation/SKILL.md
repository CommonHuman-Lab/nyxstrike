---
name: documentation
description: Systematic codebase analysis and comprehensive technical documentation generation for software projects
---

# documentation

Software architecture and implementation documentation workflow for NyxStrike. Use this skill when a user needs comprehensive technical documentation for a software project, including architecture analysis, component documentation, and detailed engineering explanations with specific code references.

## Workflow

### 1. Project Discovery & Initial Analysis

**Objective**: Understand the project's purpose, structure, and entry points.

**Steps**:
1. **Read project metadata**: Examine `README.md`, `package.json`, `pyproject.toml`, `Cargo.toml`, `setup.py`, etc.
   ```
   read(filePath="README.md")
   glob(pattern="package.json")
   glob(pattern="*.toml")
   glob(pattern="setup.py")
   ```

2. **Identify entry points**: Find main application files, server entry points, CLI tools.
   ```
   grep(pattern="def main|if __name__|app.run|app.start", include="*.py")
   glob(pattern="src/main.*")
   glob(pattern="app/*.py")
   ```

3. **Map directory structure**: Understand organization of source code, tests, configuration, assets.
   ```
   glob(pattern="src/**/*")
   glob(pattern="lib/**/*")
   glob(pattern="tests/**/*")
   ```

4. **Analyze dependencies**: Identify external libraries and frameworks.
   ```
   read(filePath="requirements.txt")
   read(filePath="package.json")
   glob(pattern="**/Cargo.toml")
   ```

### 2. Architecture Analysis

**Objective**: Reverse-engineer system architecture, layers, and data flow.

**Steps**:
1. **Identify architectural patterns**: MVC, microservices, client-server, event-driven, etc.
   - Look for directory patterns: `controllers/`, `models/`, `views/`, `services/`, `api/`
   ```
   glob(pattern="**/controllers/**/*")
   glob(pattern="**/models/**/*")
   glob(pattern="**/services/**/*")
   ```

2. **Map data flow**: Understand how data moves through the system.
   - Trace API endpoints to business logic to data storage
   ```
   grep(pattern="@app.route|@blueprint|route.*(", include="*.py")
   grep(pattern="app.get|app.post|app.put", include="*.js")
   ```

3. **Identify core components**: Find key modules, classes, and their responsibilities.
   ```
   grep(pattern="class.*:", include="*.py")
   grep(pattern="export class|export default class", include="*.ts")
   ```

4. **Analyze configuration system**: How the application is configured.
   ```
   glob(pattern="config/**/*")
   glob(pattern="*.env*")
   read(filePath="config.py")
   ```

### 3. Implementation Documentation

**Objective**: Extract detailed implementation specifics with code references.

**Steps**:
1. **Document key classes and functions**: For each major component, document:
   - Purpose and responsibility
   - Public interface (methods, properties)
   - Dependencies and interactions
   - Example usage

2. **Extract code patterns**: Identify common patterns, conventions, and idioms.
   - Error handling patterns
   - Logging strategies
   - Data validation approaches
   - Security implementations

3. **Map dependencies**: Create dependency graphs between modules.
   ```
   grep(pattern="import|from.*import", include="*.py")
   grep(pattern="require|import.*from", include="*.js")
   ```

4. **Identify external integrations**: APIs, databases, message queues, caches.
   ```
   grep(pattern="requests.get|fetch|axios", include="*.py")
   grep(pattern="mysql|postgres|redis|mongodb", include="*.py")
   ```

### 4. Documentation Synthesis

**Objective**: Create comprehensive technical documentation following the standard format.

**Documentation Template**:

```
# [Project Name] Technical Documentation

## 1. Project Overview

### Simple Overview
[High-level description of the project's purpose and key features]

### Detailed Engineering Explanation
[Specific architecture details with code references, e.g., file.py:line]

## 2. System Architecture

### Simple Overview
[High-level architectural description]

### Detailed Engineering Explanation
[Detailed architecture with component diagrams, data flow, specific file references]

## 3. Core Components

### Simple Overview
[Overview of main components]

### Detailed Engineering Explanation
[Detailed component documentation with class/method references]

## 4. [Additional Sections as Needed]
- Configuration
- Deployment
- Development Guide
- API Reference
- Data Models
- Security Considerations

## Appendix: File Reference Index
[List of key files with descriptions]
```

**Documentation Standards**:
1. **Every section must have**: Simple overview + Detailed engineering explanation
2. **Code references**: Always include specific file:line references (e.g., `src/app.py:45`)
3. **Be precise**: Reference actual code, not just concepts
4. **Be comprehensive**: Cover all major aspects of the project
5. **Be structured**: Follow logical progression from high-level to details

### 5. Quality Assurance

**Objective**: Ensure documentation accuracy and completeness.

**Steps**:
1. **Verify code references**: Ensure all file:line references are correct
2. **Check coverage**: All major components and flows should be documented
3. **Validate accuracy**: Technical details should match actual implementation
4. **Review structure**: Documentation should follow the template
5. **Test usability**: Documentation should enable understanding and contribution

## Tool Usage Guide

### For Code Analysis:
- **`glob(pattern="**/*.py")`**: Find all Python files
- **`grep(pattern="class.*:", include="*.py")`**: Find class definitions
- **`read(filePath="key_file.py")`**: Read and analyze specific files
- **`bash(command="find . -name '*.js' -type f")`**: Alternative file discovery

### For Architecture Mapping:
- Look for architectural patterns in directory structure
- Trace imports to understand module dependencies
- Follow data flow through function calls

### For Documentation:
- Use the provided template consistently
- Include specific code references for every engineering claim
- Balance overview with detailed explanations

## Example Documentation Sections

### For a Web Application:
1. **Project Overview** - Purpose, tech stack, deployment
2. **System Architecture** - Client/server, API layer, database
3. **Frontend Components** - React components, state management
4. **Backend Services** - API endpoints, business logic, data access
5. **Data Models** - Database schema, ORM models
6. **Configuration** - Environment variables, config files
7. **Development Workflow** - Building, testing, deployment
8. **Security** - Authentication, authorization, input validation

### For a Security Tool (like NyxStrike):
1. **Project Overview** - Purpose, target users, key features
2. **System Architecture** - Multi-layer design, tool integration
3. **Core Components** - Command execution, process management, intelligence engine
4. **Tool Integration** - API endpoints, MCP wrappers, registry
5. **Intelligence System** - Target profiling, tool scoring, attack chains
6. **UI Layer** - Frontend structure, real-time features
7. **Deployment** - Installation, configuration, scaling
8. **Development** - Adding tools, testing, contribution

## Common Pitfalls & Solutions

**Pitfall 1: Missing code references**
- **Solution**: Always include file:line numbers for specific implementations

**Pitfall 2: Too high-level or too detailed**
- **Solution**: Use the two-part structure (overview + detailed engineering)

**Pitfall 3: Incomplete coverage**
- **Solution**: Follow the workflow phases systematically

**Pitfall 4: Outdated information**
- **Solution**: Base documentation on current code, not assumptions

**Pitfall 5: Poor organization**
- **Solution**: Use the standard template and logical progression

## Success Metrics

Quality documentation should enable:
1. **New developers** to understand the codebase quickly
2. **Contributors** to make changes confidently
3. **Operators** to deploy and maintain the system
4. **Security reviewers** to assess the architecture
5. **AI agents** to interact with the system effectively

## NyxStrike Integration

When documenting NyxStrike or similar tools:
- Reference the existing NyxStrike documentation as an example
- Use NyxStrike's own tools for analysis when appropriate
- Follow the patterns established in the codebase
- Highlight unique architectural decisions

---
*Documentation Skill v1.0 | Based on NyxStrike Documentation Pattern*