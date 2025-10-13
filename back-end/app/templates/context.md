# 📄 ContextPilot — Contexto Atual

## 🎯 Visão geral
- Projeto: ContextPilot (framework de gerenciamento de escopo e contexto com LLMs)
- Status: Ativo, preparado para hackathon
- Objetivo: Centralizar gestão de contexto para facilitar retomadas, branchs de experimentos e controle de milestones.

## 💡 Decisão chave
- O ContextPilot será usado para armazenar o próprio contexto do desenvolvimento dele mesmo.
- Caso o SaaS não finalize a tempo, o ContextPilot será pivotado para submission no World Hackathon.

## 🚀 Estado atual
- Migration clean no Supabase concluída e testada.
- Sistema de workspaces e memberships pronto (RLS revisada).
- Frontend separado no repo `contextpilot-compass-ui`.
- CLI em Python com Typer funcionando.
- API REST com FastAPI ativa.
- UI React integrada com API (Lovable + adaptações manuais).

## 🧩 Componentes principais
- FastAPI para API principal
- Typer CLI
- React UI separada
- Supabase DB com RLS
- TUI (Text UI) preliminar

## 🟢 Próximos passos imediatos
- Consolidar arquivos de contexto.
- Integrar snapshot ao fluxo principal do ContextPilot.
- Preparar pitch rápido (PDF ou Markdown).

---
