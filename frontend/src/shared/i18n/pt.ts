// Every visible text of the interface, in Portuguese (REQ-PLT-006, §8.6).
export const pt = {
  app: {
    name: "Sextante",
    tagline: "Codificação de linhas de facturas de fornecedores",
  },
  login: {
    title: "Entrar",
    description: "Indique o token de acesso que lhe foi atribuído.",
    tokenLabel: "Token de acesso",
    submit: "Entrar",
    submitting: "A entrar…",
    tokenRequired: "Indique o token de acesso.",
    tokenTooLong: "O token é demasiado longo.",
  },
  home: {
    title: "Estado do servidor",
    serverStatus: "Servidor",
    serverUp: "Disponível",
    serverDown: "Indisponível",
    catalogDigest: "Versão do catálogo",
    loading: "A carregar…",
    logout: "Sair",
    loggingOut: "A sair…",
  },
  errors: {
    unexpected: "Não foi possível contactar o servidor. Tente de novo.",
  },
} as const;
