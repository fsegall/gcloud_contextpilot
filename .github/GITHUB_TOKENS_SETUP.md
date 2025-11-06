# GitHub Tokens Setup

## Secrets Required

Este workflow precisa de dois tokens configurados nos GitHub Secrets:

### 1. `GITHUB_TOKEN_PAT` (Principal)
- **Uso**: Criar PRs no repositório principal
- **Permissões necessárias**:
  - `repo` (acesso completo)
  - `workflow` (para disparar workflows)

### 2. `SANDBOX_REPO_TOKEN` (Sandbox)
- **Uso**: Criar PRs no repositório sandbox (`fsegall/contextpilot-sandbox`)
- **Permissões necessárias**:
  - `repo` (acesso completo)
  - `workflow` (para disparar workflows)

## Como criar um Personal Access Token (PAT)

1. Acesse: https://github.com/settings/tokens
2. Clique em "Generate new token" → "Generate new token (classic)"
3. Dê um nome descritivo (ex: "ContextPilot Actions")
4. Selecione as permissões:
   - ✅ `repo` (todas as sub-permissões)
   - ✅ `workflow`
5. Clique em "Generate token"
6. **Copie o token imediatamente** (não será mostrado novamente)

## Como atualizar os Secrets

1. Vá para o repositório: https://github.com/fsegall/gcloud_contextpilot/settings/secrets/actions
2. Para cada secret:
   - Se não existir: Clique em "New repository secret"
   - Se já existir: Clique no secret → "Update"
3. Cole o token e salve

## Verificar se está funcionando

Após atualizar, teste aprovando uma proposal e verifique se:
- ✅ O workflow é disparado
- ✅ O PR é criado no sandbox (se for proposta sandbox)
- ✅ O PR é criado no repo principal

## Troubleshooting

### Erro 403: "GitHub Actions is not permitted to create pull requests"
- Verifique se o token tem permissão `repo`
- Verifique se a configuração do repositório permite Actions criar PRs:
  - Settings → Actions → General → Workflow permissions
  - Deve estar em "Read and write permissions"

### Token expirado
- Tokens clássicos podem expirar se configurados com data de expiração
- Crie um novo token e atualize o secret

