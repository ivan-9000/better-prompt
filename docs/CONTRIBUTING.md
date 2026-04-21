# 🤝 Contributing to Better Prompt

Thank you for your interest in contributing.
This guide explains how to get set up and submit changes.

---

## Getting Started

**1. Fork the repository**

Click the **Fork** button on GitHub to create your own copy.

**2. Clone your fork**

    git clone https://github.com/your-username/better-prompt.git
    cd better-prompt

**3. Create a virtual environment**

    python -m venv .venv
    .venv\Scripts\activate      # Windows
    source .venv/bin/activate   # Mac / Linux

**4. Install dependencies**

    pip install -r requirements.txt

**5. Add your API key**

    cp .env.example .env

Edit `.env` and add your Groq key.

**6. Run the app locally**

    streamlit run app/main.py

---

## Branching Strategy

Always create a feature branch from `main`. Never commit directly
to `main`.

    git checkout -b feat/your-feature-name

Branch naming convention:

    feat/short-description     ← new feature
    fix/short-description      ← bug fix
    docs/short-description     ← documentation only
    refactor/short-description ← code restructure
    chore/short-description    ← maintenance

---

## Commit Message Convention

We follow the Conventional Commits standard.

    <type>(<scope>): <short description>

Examples:

    feat(enhance): add follow-up refinement input
    fix(runner): handle groq rate limit error
    docs(readme): add deployment screenshot
    chore(deps): update litellm to latest version

Rules:
- Use present tense: "add feature" not "added feature"
- Keep the description under 72 characters
- No capital first letter, no period at the end

---

## Running Tests

    pytest tests/

All tests must pass before opening a pull request.

---

## Opening a Pull Request

1. Push your branch to your fork:

       git push origin feat/your-feature-name

2. Go to the original repo on GitHub
3. Click **Compare & pull request**
4. Fill in the PR description:
   - What does this change do?
   - Why is it needed?
   - Any screenshots if it affects the UI
5. Click **Create pull request**

---

## Code Style

- Follow PEP 8
- Use type hints on all function signatures
- Add a docstring to every public function and class
- Keep functions short and focused — one responsibility each

---

## Questions

Open an issue on GitHub and label it `question`.
