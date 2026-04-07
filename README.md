# 📊 Projeto Integrador — VendaMais Distribuidora Ltda.

Plataforma de Inteligência Operacional • ERP → Azure → Power BI

Disciplina: **Design e Arquitetura de Software II**

Semestre: **7º Semestre — 2026/1**

Professor: **Christiano Piccinin**

---

## 👥 Integrantes da Equipe

| Nome             | GitHub                                |
| ---------------- | ------------------------------------- |
| Carlos Tomasi    | https://github.com/TomasiCarlos       |
| Gustavo Antonius | https://github.com/guarannius-estudos |
| Leonardo Latzke  | https://github.com/                   |
| Renan Apolinario | https://github.com/                   |

## 🎯 Descrição do Projeto

A VendaMais Distribuidora Ltda. enfrenta dificuldades na obtenção de indicadores operacionais atualizados devido à consolidação manual de dados provenientes do ERP.

Esta solução propõe uma plataforma de inteligência operacional baseada em serviços Azure, permitindo ingestão, transformação, armazenamento e visualização de dados com defasagem máxima de 24 horas.

ERP → Azure Functions → Blob Storage → Azure Functions → Azure SQL Database → Power BI

## 📂 Estrutura do Repositório

```
.
├── docs
│   ├── c4
│   │   ├── 01-context.png
│   │   └── 02-container.png
│   │
│   └── adr
│       ├── ADR001.md
│       └── ADR002.md
│
└── README.md
```

## 🚀 Como Navegar na Documentação

1. Acesse `docs/c4` para diagramas C4
2. Acesse `docs/adr` para ADRs (Architecture Decision Records)