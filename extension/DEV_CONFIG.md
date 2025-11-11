# Configuração para Desenvolvimento

## Serviço Dev no Cloud Run

O serviço de desenvolvimento foi deployado em:
- **URL**: `https://contextpilot-backend-dev-l7g6shydza-uc.a.run.app`
- **Serviço**: `contextpilot-backend-dev`
- **Branch**: `after-hackathon-delivery`
- **Modo**: `GITHUB_ACTION_MODE=dev`

## Como Configurar a Extensão para Usar o Serviço Dev

### Opção 1: Via Settings UI (Recomendado)

1. Abrir Settings do VS Code/Cursor:
   - `Cmd+,` (Mac) ou `Ctrl+,` (Windows/Linux)
   - Ou `Cmd+Shift+P` → "Preferences: Open Settings"

2. Procurar por "ContextPilot API URL"

3. Alterar para:
   ```
   https://contextpilot-backend-dev-l7g6shydza-uc.a.run.app
   ```

4. Recarregar a janela:
   - `Cmd+Shift+P` → "Developer: Reload Window"

### Opção 2: Via Settings JSON

1. Abrir Settings JSON:
   - `Cmd+Shift+P` (ou `Ctrl+Shift+P`)
   - Digite: "Preferences: Open Settings (JSON)"

2. Adicionar/alterar:
   ```json
   {
     "contextpilot.apiUrl": "https://contextpilot-backend-dev-l7g6shydza-uc.a.run.app"
   }
   ```

3. Salvar e recarregar a janela

## Verificar Configuração

Para verificar se está usando o serviço dev:

1. Abrir Command Palette: `Cmd+Shift+P`
2. Executar: "ContextPilot: Show Backend Configuration"
3. Verificar se a URL mostrada é a do dev

## Alternar Entre Dev e Produção

### Usar Dev:
```json
{
  "contextpilot.apiUrl": "https://contextpilot-backend-dev-l7g6shydza-uc.a.run.app"
}
```

### Usar Produção:
```json
{
  "contextpilot.apiUrl": "https://contextpilot-backend-581368740395.us-central1.run.app"
}
```

## Diferenças Entre Dev e Produção

| Feature | Produção | Dev |
|---------|----------|-----|
| Serviço | `contextpilot-backend` | `contextpilot-backend-dev` |
| Branch | `main` | `after-hackathon-delivery` |
| GitHub Actions | `apply-proposal.yml` | `apply-proposal-dev.yml` |
| Base Branch para PRs | `main` | `after-hackathon-delivery` |
| Ambiente | `production` | `development` |
| GITHUB_ACTION_MODE | `production` (padrão) | `dev` |

## Testar Conexão

Para testar se a extensão está conectada ao serviço dev:

1. Abrir Command Palette: `Cmd+Shift+P`
2. Executar: "ContextPilot: Connect to Backend"
3. Verificar se aparece mensagem de sucesso
4. Verificar status bar (canto inferior direito)

## Troubleshooting

### Extensão não conecta ao dev:
- Verificar se a URL está correta nas settings
- Verificar se o serviço dev está rodando: `gcloud run services describe contextpilot-backend-dev --region us-central1`
- Verificar logs: `gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=contextpilot-backend-dev" --limit 50`

### Erro 404 ou 500:
- Verificar se o deploy foi feito corretamente
- Verificar se todas as variáveis de ambiente estão configuradas
- Verificar logs do Cloud Run

### GitHub Actions não disparam:
- Verificar se `GITHUB_ACTION_MODE=dev` está configurado no serviço dev
- Verificar se o workflow `apply-proposal-dev.yml` existe no repositório
- Verificar se o token do GitHub tem permissões corretas

