# laddro-career

Python SDK for the [Laddro Career API](https://api.laddro.com/reference).

## Install

```bash
pip install laddro-career
```

## Usage

```python
from laddro_career import Laddro, TailorRequest

laddro = Laddro("laddro_live_...")

# List resumes
result = await laddro.resumes.list()
for resume in result.items:
    print(resume.title)

# Tailor a resume
pdf = await laddro.tailor.run(TailorRequest(
    position_name="Senior Frontend Engineer",
    job_url="https://jobs.example.com/senior-frontend",
))

# Stream progress
async for event in await laddro.tailor.stream(TailorRequest(
    position_name="Senior Frontend Engineer",
    job_description="We are looking for...",
)):
    if event.event == "progress":
        print(event.data)

# Generate cover letter
pdf = await laddro.cover_letters.generate(GenerateCoverLetterRequest(
    position_name="Product Manager",
    job_url="https://jobs.example.com/pm",
))

# Export as PDF
from laddro_career import ExportRequest
pdf = await laddro.export.pdf(ExportRequest(
    resume_id="abc-123",
    template_id="GRAPHITE",
))

# Browse templates (no auth)
laddro = Laddro()
templates = await laddro.templates.list()

# Configure BYOK
from laddro_career import UpdateAISettingsRequest
await laddro.settings.update_model(UpdateAISettingsRequest(
    provider="Anthropic",
    model="claude-sonnet-4-20250514",
    api_key="sk-ant-...",
))
```

## File uploads

```python
from pathlib import Path

pdf = await laddro.resumes.parse(
    Path("./resume.pdf"),
    template_id="GRAPHITE",
)

tailored = await laddro.tailor.upload(
    Path("./resume.pdf"),
    position_name="Backend Engineer",
    job_url="https://jobs.example.com/backend",
)
```

## Error handling

```python
from laddro_career import LaddroAPIError, LaddroAuthError, LaddroUsageLimitError

try:
    await laddro.tailor.run(request)
except LaddroUsageLimitError:
    print("Buy more credits at developers.laddro.com")
except LaddroAuthError:
    print("Invalid API key")
except LaddroAPIError as e:
    print(f"Error {e.status}: {e}")
```

## License

MIT
