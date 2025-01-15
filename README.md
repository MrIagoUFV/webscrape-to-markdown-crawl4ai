# Webscrape to Markdown - Crawl4AI

Ferramenta Python para fazer web scraping de páginas e converter automaticamente para markdown. Suporta tanto scraping de página única quanto múltiplas páginas via sitemap.xml.

## 🚀 Funcionalidades

- Scraping de página única com salvamento automático no clipboard
- Scraping de múltiplas páginas via sitemap.xml
- Conversão automática para markdown
- Gerenciamento de memória e processamento paralelo
- Cache inteligente para otimização

## 📋 Pré-requisitos

```bash
# Instale as dependências
pip install -r requirements.txt

# Instale o playwright (necessário para o crawl4ai)
playwright install
```

## 🎯 Como Usar

### Scraping de Página Única

```python
# Execute o script
python codigos/uma_pagina.py
```

O conteúdo será automaticamente convertido para markdown e copiado para seu clipboard.

### Scraping de Múltiplas Páginas

```python
# Execute o script
python codigos/multiplas_paginas.py
```

1. Digite a URL do sitemap quando solicitado
2. O script irá:
   - Extrair todas as URLs do sitemap
   - Processar as páginas em paralelo
   - Salvar os arquivos markdown na pasta `/docs`
   - Gerar um README.md na pasta `/docs` com links para todas as páginas processadas

## 📁 Estrutura do Projeto

```
.
├── codigos/
│   ├── uma_pagina.py           # Script para página única
│   ├── multiplas_paginas.py    # Script para múltiplas páginas
│   └── multiplas_paginas_manual.py
├── docs/                       # Arquivos markdown gerados
├── requirements.txt            # Dependências do projeto
└── README.md                   # Este arquivo
```

## 🛠️ Tecnologias Utilizadas

- Python
- crawl4ai
- playwright
- psutil
- pyperclip

## ⚙️ Configurações

O projeto inclui configurações otimizadas para:
- Processamento paralelo (máximo de 10 páginas simultâneas)
- Gerenciamento automático de memória
- Modo headless do navegador
- Sistema de cache inteligente
