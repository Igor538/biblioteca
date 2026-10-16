import os
import smtplib
import ssl
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "").replace(" ", "")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "no-reply@biblioteca.local")
EMAIL_FROM_NAME = os.environ.get("EMAIL_FROM_NAME", "Biblioteca Digital")


def smtp_configurado():
    return bool(SMTP_HOST)


def _remetente():
    if EMAIL_FROM_NAME:
        return f"{Header(EMAIL_FROM_NAME, 'utf-8')} <{EMAIL_FROM}>"
    return EMAIL_FROM


def montar_email_recuperacao(nome, link, horas):
    """Monta o e-mail de recuperacao de senha.

    Retorna uma tupla (texto, html) com as duas versoes da mensagem.
    """
    saudacao = f"Olá, {nome}!" if nome else "Olá!"

    texto = f"""{saudacao}

Recebemos um pedido para redefinir a senha da sua conta na Biblioteca Digital.

Acesse o link abaixo para criar uma nova senha:
{link}

O link expira em {horas} hora(s). Se você não solicitou a redefinição, ignore este e-mail.
"""

    html = f"""<!doctype html>
<html lang="pt-BR">
<body style="margin:0;padding:0;background:#eef1f7;font-family:'Segoe UI',Roboto,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#eef1f7;padding:32px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:520px;background:#ffffff;border-radius:14px;overflow:hidden;box-shadow:0 4px 18px rgba(31,78,121,0.12);">
          <tr>
            <td style="background:#1f4e79;padding:26px 32px;">
              <span style="color:#ffffff;font-size:20px;font-weight:700;letter-spacing:.3px;">📚 Biblioteca Digital</span>
            </td>
          </tr>
          <tr>
            <td style="padding:32px;color:#2b3440;font-size:15px;line-height:1.65;">
              <p style="margin:0 0 16px;font-size:16px;">{saudacao}</p>
              <p style="margin:0 0 16px;">Recebemos um pedido para <strong>redefinir a senha</strong> da sua conta.</p>
              <p style="margin:0 0 28px;">Para criar uma nova senha, clique no botão abaixo:</p>
              <table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 auto 28px;">
                <tr>
                  <td align="center" style="border-radius:9px;background:#1f4e79;">
                    <a href="{link}" target="_blank" style="display:inline-block;padding:14px 34px;color:#ffffff;font-size:15px;font-weight:600;text-decoration:none;border-radius:9px;">Redefinir minha senha</a>
                  </td>
                </tr>
              </table>
              <p style="margin:0 0 8px;font-size:13px;color:#6b7683;">Este link expira em <strong>{horas} hora(s)</strong>.</p>
              <p style="margin:0;font-size:13px;color:#6b7683;">Se você não solicitou a redefinição, ignore este e-mail com segurança.</p>
            </td>
          </tr>
          <tr>
            <td style="background:#f2f4f9;padding:18px 32px;color:#96a0ad;font-size:12px;text-align:center;">
              Esta é uma mensagem automática — não responda a este e-mail.
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    return texto, html


def enviar_email(destino, assunto, corpo_texto, corpo_html=None):
    """Envia e-mail via SMTP.

    Retorna True quando o e-mail e efetivamente enviado. Retorna False
    quando o SMTP nao esta configurado (modo desenvolvimento) ou quando o
    envio falha.
    """
    if not smtp_configurado():
        print(f"[EMAIL] SMTP nao configurado. Destinatario: {destino} | Assunto: {assunto}")
        print(f"[EMAIL] Corpo: {corpo_texto}")
        return False
    try:
        mensagem = MIMEMultipart("alternative")
        mensagem["From"] = _remetente()
        mensagem["To"] = destino
        mensagem["Subject"] = Header(assunto, "utf-8")
        mensagem.attach(MIMEText(corpo_texto, "plain", "utf-8"))
        if corpo_html:
            mensagem.attach(MIMEText(corpo_html, "html", "utf-8"))
        contexto = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as servidor:
            servidor.starttls(context=contexto)
            if SMTP_USER:
                servidor.login(SMTP_USER, SMTP_PASS)
            servidor.sendmail(EMAIL_FROM, [destino], mensagem.as_string())
        return True
    except Exception as erro:
        print(f"[EMAIL] Falha ao enviar para {destino}: {erro}")
        return False
