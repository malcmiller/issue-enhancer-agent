# Issue Enhancer Agent

An AI-powered GitHub Action that enhances issue descriptions, comments, and labels using Semantic Kernel and Azure OpenAI.

## Features

- Automatically generates AI-enhanced summaries for GitHub issues
- Suggests relevant labels (e.g., bug, enhancement, good first issue)
- Adds comments and labels to issues using the GitHub API
- Uses Azure OpenAI via Semantic Kernel for natural language processing

## Usage

### Inputs

- `github_token`: GitHub token with repo access
- `openai_api_key`: API key for Azure OpenAI
- `azure_openai_endpoint`: Azure OpenAI endpoint URL (e.g., `https://<your-resource>.openai.azure.com/`)
- `azure_openai_deployment`: Azure OpenAI deployment name
- `issue_id`: Unique ID of the GitHub issue
- `issue_title`: Title of the GitHub issue
- `issue_body`: Main description or content of the GitHub issue

### Outputs

- `enhanced_summary`: AI-generated summary or insight about the issue

## Using as a GitHub Marketplace Action

You can use Issue Enhancer Agent directly from the GitHub Marketplace in your workflows. Add the following step to your workflow YAML:

```yaml
- name: Enhance GitHub Issue
  uses: malcmiller/issue-enhancer-agent@v1
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    openai_api_key: ${{ secrets.OPENAI_API_KEY }}
    azure_openai_endpoint: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
    azure_openai_deployment: ${{ secrets.AZURE_OPENAI_DEPLOYMENT }}
    issue_id: ${{ github.event.issue.number }}
    issue_title: ${{ github.event.issue.title }}
    issue_body: ${{ github.event.issue.body }}
```

### Notes

- Make sure to add the required secrets to your repository.
- The action will automatically comment and label the issue with AI-generated insights.
- You can use this action in workflows triggered by issues, such as `issues` or `issue_comment` events.

## Development

### Requirements

- Python 3.11+
- Docker
- Azure OpenAI resource and deployment
- GitHub token with repo access

### Setup

1. Clone the repository
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Build the Docker image:

   ```bash
   docker build -t issue-enhancer-agent .
   ```

4. Run the agent locally (set required environment variables):

   ```bash
   docker run --rm \
     -e INPUT_GITHUB_TOKEN=your_token \
     -e INPUT_OPENAI_API_KEY=your_openai_key \
     -e INPUT_AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/ \
     -e INPUT_AZURE_OPENAI_DEPLOYMENT=your_deployment \
     -e INPUT_ISSUE_ID=1 \
     -e INPUT_ISSUE_TITLE="Test Issue" \
     -e INPUT_ISSUE_BODY="Test body" \
     -e INPUT_GITHUB_REPOSITORY=owner/repo \
     issue-enhancer-agent
   ```

## License

MIT
