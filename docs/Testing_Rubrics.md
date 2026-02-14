# Testing Rubrics: AI Skills Builder

## 1. Unit Testing Rubric

| Component | Test Case | Success Criteria |
|-----------|-----------|------------------|
| OCR Engine | Detect "Ask AI" text on image | Correct coordinates $(\pm 10px)$ |
| Browser Controller | Navigate to URL | Page title matches expected |
| Image Processor | Grayscale conversion | Histogram shows reduced color depth |
| Skill Formatter | JSON output generation | Valid JSON schema |

## 2. Integration Testing Rubric

| Scenario | Execution Steps | Success Criteria |
|----------|-----------------|------------------|
| End-to-End Skill Build | Start script -> Finish skill | Skill file exists and contains relevant text |
| Theme Toggle | Toggle mode | OCR detects "Dark" text or specific element color change |
| Chat Interaction | Send query -> Wait -> Read | Read text is not empty and matches expected response pattern |
| Error Handling | Navigate to 404 site | Script terminates with "Site not found" error |

## 3. Performance & Token Rubric

| Metric | Target | Method |
|--------|--------|--------|
| OCR Latency | < 5s per frame | Timing logs |
| Token Usage (Input) | < 1000 tokens | API usage logs (if applicable) |
| Token Usage (Output) | < 500 tokens | Skill file character count |
| Accuracy | > 95% | Manual verification of first 10 runs |
