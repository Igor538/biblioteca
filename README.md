# 📚 Biblioteca

Sistema de gerenciamento de biblioteca feito em **Flask** com **PostgreSQL**, com controle de empréstimos, devoluções, reservas, penalidades, notificações e auditoria — além de recuperação de senha por e-mail e consulta pública do acervo (sem login).

## ✨ Funcionalidades

| Módulo | O que faz |
| ------ | --------- |
| 🔐 Login e perfis | Administrador, Bibliotecário e Leitor com permissões diferentes |
| 🔑 Recuperação de senha | Envia um link por e-mail para redefinir a senha (válido por 1 hora) |
| 🔎 Catálogo público | Consulta ao acervo sem precisar de login |
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

Crie um arquivo `.env` na raiz do projeto. A `DATABASE_URL` é obrigatória (o sistema usa PostgreSQL); as demais são opcionais:

| Variável | Obrigatória | Descrição |
| -------- | :---------: | --------- |
| `DATABASE_URL` | sim | String de conexão do PostgreSQL (Neon/Supabase) |
| `SECRET_KEY` | recomendada | Chave das sessões do Flask |
| `APP_BASE_URL` | recomendada | URL pública do sistema, usada no link enviado por e-mail |
| `SMTP_HOST` | não | Servidor SMTP para envio de e-mails |
| `SMTP_PORT` | não | Porta SMTP (padrão `587`) |
| `SMTP_USER` | não | Usuário/login do SMTP |
| `SMTP_PASS` | não | Senha do SMTP |
| `EMAIL_FROM` | não | Endereço remetente |
| `EMAIL_FROM_NAME` | não | Nome exibido do remetente (padrão `Biblioteca Digital`) |
| `DB_POOL_SIZE` | não | Número máximo de conexões no pool (padrão `5`) |
| `MOSTRAR_LINK_RECUPERACAO` | não | `1` mostra o link de redefinição na tela (apenas desenvolvimento) |

### 📧 Recuperação de senha

Sem `SMTP_HOST`, o sistema entra em **modo desenvolvimento**: o e-mail é registrado no console e o link **não** aparece na tela (só aparece se `MOSTRAR_LINK_RECUPERACAO=1`). Com o SMTP configurado, a mensagem é enviada por e-mail.

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

## ☁️ Deploy (Vercel)

O projeto já inclui o `entrypoint` para a Vercel (`servidor.app:app`). Cadastre as variáveis de ambiente da tabela acima em **Settings → Environment Variables** — o `.env` não vai para o repositório.

## 🗂️ Estrutura

```
biblioteca/
├── banco/           # esquema SQL (PostgreSQL)
├── cliente/         # templates HTML e arquivos estáticos
└── servidor/        # aplicação Flask, rotas e modelos
```
