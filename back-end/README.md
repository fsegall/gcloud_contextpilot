# 🧠 ContextPilot

**ContextPilot** é um framework leve para gerenciamento de escopo e progresso em projetos de software, com integração a LLMs, histórico Git e suporte a múltiplos projetos via `workspace_id`.

---

## 🚀 Instalação

```bash
git clone https://github.com/seu-usuario/contextpilot.git
cd contextpilot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # configure sua OPENAI_API_KEY
