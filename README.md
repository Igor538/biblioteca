# 📚 Biblioteca

Sistema de gerenciamento de biblioteca feito em **Flask + SQLite**, com controle de empréstimos, devoluções, reservas, penalidades, notificações e auditoria.

## ✨ Funcionalidades

| Módulo | O que faz |
| ------ | --------- |
| 🔐 Login e perfis | Administrador, Bibliotecário e Leitor com permissões diferentes |
| 📖 Livros | Cadastro e consulta do acervo |
| 👥 Usuários | Gestão de contas e perfis (somente staff) |
| 📤 Empréstimos | Empréstimos, renovações e devoluções |
| ↩️ Devoluções | Registro e cálculo de atrasos |
| 🔖 Reservas | Fila de reservas por livro |
| 🔔 Notificações | Avisos de atraso, retirada e sistema |
| 📊 Relatórios | Dashboard e relatórios gerenciais |
| 📝 Auditoria | Registro de todas as operações |
| 🛠️ Serviços | Solicitações de serviços aos usuários |

## 🚀 Como rodar

```bash
pip install -r requirements.txt
cd servidor
python app.py
```

Acesse: **http://127.0.0.1:5000**

Na primeira execução, o banco de dados (`banco/biblioteca.db`) é criado automaticamente a partir de `banco/esquema.sql`, com dados de exemplo.

## 🔑 Contas padrão

| E-mail | Senha | Perfil |
| ------ | ----- | ------ |
| `admin@biblioteca.local` | `admin` | Administrador |
| `bibliotecaria@biblioteca.local` | `biblioteca` | Bibliotecária |

Novas contas criadas pelo cadastro público entram como **Leitor**.

## 🧭 O que cada perfil vê

- **Administrador** — acesso total, incluindo auditoria e backup.
- **Bibliotecário** — gestão do acervo, empréstimos, devoluções, reservas e relatórios.
- **Leitor** — consulta ao acervo, suas reservas, seu histórico e suas notificações.

## 🗂️ Estrutura

```
bibliotecas/
├── banco/           # esquema SQL e banco SQLite
├── cliente/         # templates HTML e arquivos estáticos
└── servidor/        # aplicação Flask, rotas e modelos
```
