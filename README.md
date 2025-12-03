# SSSTI
Sistema de Solicitações de Suporte de TI

graph TB
    subgraph "Cliente"
        A[👤 Usuário/Cliente]
    end
    
    subgraph "Amazon S3"
        B[🌐 Landing Page<br/>Site Estático]
        C[📁 Bucket de Arquivos<br/>Uploads/Anexos]
    end
    
    subgraph "Amazon API Gateway"
        D[🔌 API REST<br/>POST /solicitacao]
    end
    
    subgraph "AWS Lambda"
        E[⚡ Função Lambda<br/>processarSolicitacao]
    end
    
    subgraph "Amazon DynamoDB"
        F[💾 Tabela: Tickets<br/>ID, Cliente, Problema, Status]
    end
    
    subgraph "Amazon SNS"
        G[📧 Tópico SNS<br/>Notificações]
        H[✉️ Email do Técnico]
    end
    
    A -->|1. Acessa| B
    A -->|2. Preenche Formulário<br/>+ Upload Arquivo| B
    B -->|3. Envia Dados| D
    D -->|4. Invoca| E
    E -->|5. Salva Arquivo| C
    E -->|6. Grava Ticket| F
    E -->|7. Publica Mensagem| G
    G -->|8. Envia Notificação| H
    
    style A fill:#e1f5ff
    style B fill:#ff9900
    style C fill:#ff9900
    style D fill:#ff4f8b
    style E fill:#ff9900
    style F fill:#4053d6
    style G fill:#ff9900
    style H fill:#90ee90
    
    classDef aws fill:#ff9900,stroke:#232f3e,stroke-width:2px,color:#fff
    classDef client fill:#e1f5ff,stroke:#232f3e,stroke-width:2px
    classDef output fill:#90ee90,stroke:#232f3e,stroke-width:2px