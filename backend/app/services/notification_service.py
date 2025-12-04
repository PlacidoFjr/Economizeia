import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.db.models import Notification, NotificationChannel, NotificationType, User
from app.core.config import settings
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import uuid
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications via email, SMS, and push."""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_from = settings.SMTP_FROM
    
    async def send_email(self, to: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """Send email notification."""
        if not self.smtp_host:
            logger.warning("SMTP not configured, skipping email")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_from
            msg['To'] = to
            
            msg.attach(MIMEText(body, 'plain'))
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent to {to}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    async def send_sms(self, to: str, message: str) -> bool:
        """Send SMS notification (placeholder - integrate with Twilio or similar)."""
        # TODO: Integrate with Twilio or SMS provider
        logger.warning("SMS not implemented yet")
        return False
    
    async def send_push(self, user_id: uuid.UUID, title: str, body: str, data: Dict = None) -> bool:
        """Send push notification (placeholder - integrate with FCM/APNs)."""
        # TODO: Integrate with FCM/APNs
        logger.warning("Push notifications not implemented yet")
        return False
    
    async def send_bill_reminder(
        self,
        db: Session,
        user: User,
        bill_id: uuid.UUID,
        issuer: str,
        amount: float,
        due_date: datetime,
        days_before: int
    ) -> Notification:
        """Send bill reminder notification."""
        message = f"Lembrete: boleto {issuer} vence em {days_before} dias. Valor R$ {amount:.2f}."
        
        # Determine channels based on user preferences
        channels = []
        if user.notif_prefs.get("email_enabled", True):
            channels.append(NotificationChannel.EMAIL)
        if user.notif_prefs.get("sms_enabled", False):
            channels.append(NotificationChannel.SMS)
        if user.notif_prefs.get("push_enabled", True):
            channels.append(NotificationChannel.PUSH)
        
        # Try to send via preferred channels
        sent = False
        sent_channel = None
        
        for channel in channels:
            if channel == NotificationChannel.EMAIL:
                # Create HTML email for bill reminder
                html_body = f"""
                <!DOCTYPE html>
                <html lang="pt-BR">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                </head>
                <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f3f4f6; line-height: 1.6;">
                    <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #f3f4f6; padding: 20px 0;">
                        <tr>
                            <td align="center" style="padding: 40px 20px;">
                                <table role="presentation" style="max-width: 600px; width: 100%; border-collapse: collapse; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden;">
                                    
                                    <!-- Header -->
                                    <tr>
                                        <td style="background: linear-gradient(135deg, #1f2937 0%, #374151 100%); padding: 30px 40px; text-align: center;">
                                            <h1 style="margin: 0 0 8px 0; color: #ffffff; font-size: 28px; font-weight: 700; letter-spacing: -0.5px; line-height: 1.2;">
                                                EconomizeIA
                                            </h1>
                                            <p style="margin: 0; color: #e5e7eb; font-size: 15px; font-weight: 400; line-height: 1.5;">
                                                Lembrete de Boleto
                                            </p>
                                        </td>
                                    </tr>
                                    
                                    <!-- Content -->
                                    <tr>
                                        <td style="padding: 40px;">
                                            <h2 style="margin: 0 0 20px 0; color: #111827; font-size: 22px; font-weight: 600; line-height: 1.3;">
                                                ⏰ Lembrete de Vencimento
                                            </h2>
                                            <p style="margin: 0 0 24px 0; color: #374151; font-size: 17px; line-height: 1.7;">
                                                Olá! Este é um lembrete de que você tem um boleto vencendo em breve.
                                            </p>
                                            
                                            <!-- Bill Info Card -->
                                            <div style="background-color: #f9fafb; border-radius: 10px; padding: 24px; margin-bottom: 24px; border-left: 4px solid #f59e0b;">
                                                <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                                    <tr>
                                                        <td style="padding-bottom: 12px;">
                                                            <p style="margin: 0; color: #6b7280; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
                                                                Emissor
                                                            </p>
                                                            <p style="margin: 4px 0 0 0; color: #111827; font-size: 18px; font-weight: 600; line-height: 1.4;">
                                                                {issuer}
                                                            </p>
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td style="padding-bottom: 12px;">
                                                            <p style="margin: 0; color: #6b7280; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
                                                                Valor
                                                            </p>
                                                            <p style="margin: 4px 0 0 0; color: #111827; font-size: 24px; font-weight: 700; line-height: 1.4;">
                                                                R$ {amount:.2f}
                                                            </p>
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td>
                                                            <p style="margin: 0; color: #6b7280; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
                                                                Vence em
                                                            </p>
                                                            <p style="margin: 4px 0 0 0; color: #dc2626; font-size: 18px; font-weight: 600; line-height: 1.4;">
                                                                {days_before} {('dia' if days_before == 1 else 'dias')}
                                                            </p>
                                                        </td>
                                                    </tr>
                                                </table>
                                            </div>
                                            
                                            <p style="margin: 0; color: #4b5563; font-size: 16px; line-height: 1.7;">
                                                Não se esqueça de realizar o pagamento para evitar juros e multas.
                                            </p>
                                        </td>
                                    </tr>
                                    
                                    <!-- Footer -->
                                    <tr>
                                        <td style="padding: 30px 40px; text-align: center; background-color: #f9fafb; border-top: 2px solid #e5e7eb;">
                                            <p style="margin: 0; color: #9ca3af; font-size: 12px; line-height: 1.6;">
                                                © 2025 EconomizeIA. Todos os direitos reservados.
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                </body>
                </html>
                """
                sent = await self.send_email(
                    user.email,
                    f"Lembrete: Boleto {issuer} vence em {days_before} dias",
                    message,
                    html_body=html_body
                )
                if sent:
                    sent_channel = channel
                    break
            elif channel == NotificationChannel.SMS and user.phone:
                sent = await self.send_sms(user.phone, message)
                if sent:
                    sent_channel = channel
                    break
            elif channel == NotificationChannel.PUSH:
                sent = await self.send_push(user.id, "Lembrete de Boleto", message)
                if sent:
                    sent_channel = channel
                    break
        
        # Create notification log
        notification = Notification(
            id=uuid.uuid4(),
            user_id=user.id,
            type=NotificationType.REMINDER,
            channel=sent_channel or channels[0] if channels else NotificationChannel.EMAIL,
            sent_at=datetime.utcnow() if sent else None,
            payload={
                "bill_id": str(bill_id),
                "issuer": issuer,
                "amount": amount,
                "due_date": due_date.isoformat(),
                "days_before": days_before
            },
            status="sent" if sent else "failed"
        )
        
        db.add(notification)
        db.commit()
        
        return notification
    
    async def schedule_reminders(
        self,
        db: Session,
        user: User,
        bill_id: uuid.UUID,
        issuer: str,
        amount: float,
        due_date: datetime,
        reminder_days: List[int]
    ):
        """Schedule reminders for a bill."""
        from app.celery_app import schedule_reminder_task
        
        for days in reminder_days:
            reminder_date = due_date - timedelta(days=days)
            if reminder_date > datetime.now().date():
                schedule_reminder_task.apply_async(
                    args=[str(user.id), str(bill_id), issuer, amount, due_date.isoformat(), days],
                    eta=reminder_date
                )
    
    async def send_welcome_email(self, user: User) -> bool:
        """Send welcome email to newly registered user."""
        try:
            # Load HTML template
            template_path = Path(__file__).parent.parent / "templates" / "email_welcome.html"
            
            if not template_path.exists():
                logger.warning(f"Welcome email template not found at {template_path}")
                # Fallback to simple text email
                return await self.send_email(
                    to=user.email,
                    subject="Bem-vindo ao EconomizeIA! 🎉",
                    body=f"""
Olá {user.name},

Bem-vindo ao EconomizeIA! Sua conta foi criada com sucesso.

Acesse o sistema e comece a organizar suas finanças:
{settings.FRONTEND_URL or 'http://localhost:3000'}/dashboard

Atenciosamente,
Equipe EconomizeIA
"""
                )
            
            # Read template
            with open(template_path, 'r', encoding='utf-8') as f:
                html_template = f.read()
            
            # Replace variables
            html_body = html_template.replace('{{name}}', user.name)
            html_body = html_body.replace('{{frontend_url}}', settings.FRONTEND_URL or 'http://localhost:3000')
            
            # Plain text version
            text_body = f"""
Olá {user.name},

Bem-vindo ao EconomizeIA! 🎉

Ficamos muito felizes em tê-lo conosco! Sua conta foi criada com sucesso e você já pode começar a organizar suas finanças de forma inteligente.

Principais funcionalidades:
• Upload Automático - Envie seus boletos e faturas. Nossa IA extrai as informações automaticamente.
• Dashboard Inteligente - Visualize seus gastos, receitas e tendências em gráficos detalhados.
• Lembretes Automáticos - Receba notificações antes dos vencimentos e nunca mais perca um pagamento.
• Assistente Virtual - Converse com nosso assistente IA para adicionar despesas e obter ajuda.

Acesse o sistema: {settings.FRONTEND_URL or 'http://localhost:3000'}/dashboard

Precisa de ajuda? Nosso assistente virtual está sempre disponível para responder suas dúvidas.

Atenciosamente,
Equipe EconomizeIA

---
Este é um email automático, por favor não responda.
© 2025 EconomizeIA. Todos os direitos reservados.
"""
            
            # Send email
            return await self.send_email(
                to=user.email,
                subject="Bem-vindo ao EconomizeIA! 🎉",
                body=text_body,
                html_body=html_body
            )
            
        except Exception as e:
            logger.error(f"Error sending welcome email to {user.email}: {e}")
            return False


    async def send_verification_email(self, user: User, verification_token: str) -> bool:
        """Send email verification email to user."""
        try:
            verification_link = f"{settings.FRONTEND_URL or 'http://localhost:3000'}/verify-email?token={verification_token}"
            
            # Load HTML template
            template_path = Path(__file__).parent.parent / "templates" / "email_verification.html"
            
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    html_template = f.read()
                
                # Replace variables
                html_body = html_template.replace('{{name}}', user.name)
                html_body = html_body.replace('{{verification_link}}', verification_link)
            else:
                # Fallback HTML
                html_body = f"""
                <!DOCTYPE html>
                <html lang="pt-BR">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                </head>
                <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f3f4f6; line-height: 1.6;">
                    <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #f3f4f6; padding: 20px 0;">
                        <tr>
                            <td align="center" style="padding: 40px 20px;">
                                <table role="presentation" style="max-width: 600px; width: 100%; border-collapse: collapse; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden;">
                                    <tr>
                                        <td style="background: linear-gradient(135deg, #1f2937 0%, #374151 100%); padding: 40px 40px; text-align: center;">
                                            <h1 style="margin: 0 0 8px 0; color: #ffffff; font-size: 32px; font-weight: 700; letter-spacing: -0.5px; line-height: 1.2;">
                                                EconomizeIA
                                            </h1>
                                            <p style="margin: 0; color: #e5e7eb; font-size: 16px; font-weight: 400; line-height: 1.5;">
                                                Confirme seu Email
                                            </p>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 50px 40px;">
                                            <h2 style="margin: 0 0 20px 0; color: #111827; font-size: 24px; font-weight: 600; line-height: 1.3;">
                                                Olá, {user.name}!
                                            </h2>
                                            <p style="margin: 0 0 20px 0; color: #374151; font-size: 17px; line-height: 1.7;">
                                                Obrigado por se cadastrar no <strong style="color: #1f2937;">EconomizeIA</strong>!
                                            </p>
                                            <p style="margin: 0 0 32px 0; color: #4b5563; font-size: 16px; line-height: 1.7;">
                                                Para completar seu cadastro e começar a usar o sistema, confirme seu endereço de email clicando no botão abaixo.
                                            </p>
                                            <table role="presentation" style="width: 100%; border-collapse: collapse; margin-bottom: 32px;">
                                                <tr>
                                                    <td align="center">
                                                        <a href="{verification_link}" style="display: inline-block; padding: 16px 40px; background-color: #1f2937; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 17px; line-height: 1.5;">
                                                            Confirmar Email →
                                                        </a>
                                                    </td>
                                                </tr>
                                            </table>
                                            <div style="background-color: #f9fafb; border-radius: 8px; padding: 20px; margin-bottom: 24px; border-left: 4px solid #3b82f6;">
                                                <p style="margin: 0 0 12px 0; color: #374151; font-size: 14px; font-weight: 600; line-height: 1.6;">
                                                    Não consegue clicar no botão?
                                                </p>
                                                <p style="margin: 0; color: #6b7280; font-size: 13px; line-height: 1.6; word-break: break-all;">
                                                    Copie e cole este link no seu navegador:<br>
                                                    <span style="color: #3b82f6;">{verification_link}</span>
                                                </p>
                                            </div>
                                            <div style="background-color: #fef3c7; border-radius: 8px; padding: 16px; border-left: 4px solid #f59e0b;">
                                                <p style="margin: 0; color: #92400e; font-size: 14px; line-height: 1.6;">
                                                    <strong>⏰ Importante:</strong> Este link é válido por <strong>24 horas</strong>. Após esse período, você precisará solicitar um novo link.
                                                </p>
                                            </div>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 40px; text-align: center; background-color: #f9fafb; border-top: 2px solid #e5e7eb;">
                                            <p style="margin: 0 0 12px 0; color: #374151; font-size: 15px; line-height: 1.6;">
                                                <strong style="color: #111827;">Não solicitou este email?</strong>
                                            </p>
                                            <p style="margin: 0; color: #6b7280; font-size: 14px; line-height: 1.6;">
                                                Se você não se cadastrou no EconomizeIA, pode ignorar este email com segurança.
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                </body>
                </html>
                """
            
            # Plain text version
            text_body = f"""
Olá {user.name},

Obrigado por se cadastrar no EconomizeIA!

Para completar seu cadastro e começar a usar o sistema, confirme seu endereço de email clicando no link abaixo:

{verification_link}

Este link é válido por 24 horas.

Se você não se cadastrou no EconomizeIA, pode ignorar este email com segurança.

Atenciosamente,
Equipe EconomizeIA
"""
            
            # Send email
            return await self.send_email(
                to=user.email,
                subject="Confirme seu email - EconomizeIA",
                body=text_body,
                html_body=html_body
            )
            
        except Exception as e:
            logger.error(f"Error sending verification email to {user.email}: {e}")
            return False


    async def send_budget_exceeded_alert(
        self,
        db: Session,
        user: User,
        monthly_income: float,
        monthly_expenses: float,
        monthly_balance: float,
        percentage_over: float
    ) -> bool:
        """Send alert when expenses exceed income."""
        if not user.notif_prefs.get("email_enabled", True):
            return False
        
        subject = f"⚠️ Atenção: Você extrapolou sua receita do mês - EconomizeIA"
        
        html_body = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f3f4f6; line-height: 1.6;">
            <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #f3f4f6; padding: 20px 0;">
                <tr>
                    <td align="center" style="padding: 40px 20px;">
                        <table role="presentation" style="max-width: 600px; width: 100%; border-collapse: collapse; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden;">
                            
                            <!-- Header -->
                            <tr>
                                <td style="background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%); padding: 40px 40px; text-align: center;">
                                    <h1 style="margin: 0 0 8px 0; color: #ffffff; font-size: 32px; font-weight: 700; letter-spacing: -0.5px; line-height: 1.2;">
                                        ⚠️ Alerta Financeiro
                                    </h1>
                                    <p style="margin: 0; color: #fee2e2; font-size: 16px; font-weight: 400; line-height: 1.5;">
                                        EconomizeIA
                                    </p>
                                </td>
                            </tr>
                            
                            <!-- Content -->
                            <tr>
                                <td style="padding: 50px 40px;">
                                    <h2 style="margin: 0 0 20px 0; color: #111827; font-size: 24px; font-weight: 600; line-height: 1.3;">
                                        Olá, {user.name}!
                                    </h2>
                                    <p style="margin: 0 0 24px 0; color: #374151; font-size: 17px; line-height: 1.7;">
                                        Detectamos que seus <strong style="color: #dc2626;">gastos ultrapassaram sua receita</strong> neste mês.
                                    </p>
                                    
                                    <!-- Financial Summary Card -->
                                    <div style="background-color: #fef2f2; border-radius: 10px; padding: 24px; margin-bottom: 24px; border-left: 4px solid #dc2626;">
                                        <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                            <tr>
                                                <td style="padding-bottom: 16px;">
                                                    <p style="margin: 0; color: #6b7280; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
                                                        Receita do Mês
                                                    </p>
                                                    <p style="margin: 4px 0 0 0; color: #059669; font-size: 20px; font-weight: 700; line-height: 1.4;">
                                                        R$ {monthly_income:.2f}
                                                    </p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td style="padding-bottom: 16px;">
                                                    <p style="margin: 0; color: #6b7280; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
                                                        Despesas do Mês
                                                    </p>
                                                    <p style="margin: 4px 0 0 0; color: #dc2626; font-size: 20px; font-weight: 700; line-height: 1.4;">
                                                        R$ {monthly_expenses:.2f}
                                                    </p>
                                                </td>
                                            </tr>
                                            <tr>
                                                <td>
                                                    <p style="margin: 0; color: #6b7280; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
                                                        Saldo
                                                    </p>
                                                    <p style="margin: 4px 0 0 0; color: #dc2626; font-size: 28px; font-weight: 700; line-height: 1.4;">
                                                        R$ {monthly_balance:.2f}
                                                    </p>
                                                    <p style="margin: 8px 0 0 0; color: #dc2626; font-size: 14px; font-weight: 600;">
                                                        Você está gastando {percentage_over:.1f}% a mais do que recebe
                                                    </p>
                                                </td>
                                            </tr>
                                        </table>
                                    </div>
                                    
                                    <div style="background-color: #fef3c7; border-radius: 8px; padding: 20px; margin-bottom: 24px; border-left: 4px solid #f59e0b;">
                                        <p style="margin: 0 0 12px 0; color: #92400e; font-size: 15px; font-weight: 600; line-height: 1.6;">
                                            💡 Recomendações:
                                        </p>
                                        <ul style="margin: 0; padding-left: 20px; color: #78350f; font-size: 14px; line-height: 1.8;">
                                            <li>Revise seus gastos e identifique onde pode economizar</li>
                                            <li>Priorize o pagamento de boletos essenciais</li>
                                            <li>Considere adiar gastos não essenciais</li>
                                            <li>Use o dashboard para analisar seus gastos por categoria</li>
                                        </ul>
                                    </div>
                                    
                                    <table role="presentation" style="width: 100%; border-collapse: collapse; margin-bottom: 24px;">
                                        <tr>
                                            <td align="center" style="padding: 0;">
                                                <a href="{settings.FRONTEND_URL or 'http://localhost:3000'}/dashboard" target="_blank" style="display: inline-block; padding: 14px 28px; background-color: #1f2937; color: #ffffff; font-size: 16px; font-weight: 600; text-decoration: none; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                                                    Ver Meu Dashboard
                                                </a>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <p style="margin: 0; color: #4b5563; font-size: 16px; line-height: 1.7;">
                                        Atenciosamente,<br>
                                        Equipe EconomizeIA
                                    </p>
                                </td>
                            </tr>
                            
                            <!-- Footer -->
                            <tr>
                                <td style="padding: 30px 40px; text-align: center; background-color: #f9fafb; border-top: 1px solid #e5e7eb;">
                                    <p style="margin: 0; color: #6b7280; font-size: 13px; line-height: 1.6;">
                                        © 2025 EconomizeIA. Todos os direitos reservados.
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        text_body = f"""
Olá {user.name},

⚠️ ALERTA: Você extrapolou sua receita do mês!

Receita do Mês: R$ {monthly_income:.2f}
Despesas do Mês: R$ {monthly_expenses:.2f}
Saldo: R$ {monthly_balance:.2f}

Você está gastando {percentage_over:.1f}% a mais do que recebe.

Recomendações:
• Revise seus gastos e identifique onde pode economizar
• Priorize o pagamento de boletos essenciais
• Considere adiar gastos não essenciais
• Use o dashboard para analisar seus gastos por categoria

Acesse seu dashboard: {settings.FRONTEND_URL or 'http://localhost:3000'}/dashboard

Atenciosamente,
Equipe EconomizeIA
"""
        
        sent = await self.send_email(user.email, subject, text_body, html_body)
        
        if sent:
            # Log notification
            notification = Notification(
                id=uuid.uuid4(),
                user_id=user.id,
                type=NotificationType.ANOMALY,
                channel=NotificationChannel.EMAIL,
                sent_at=datetime.utcnow(),
                payload={
                    "monthly_income": monthly_income,
                    "monthly_expenses": monthly_expenses,
                    "monthly_balance": monthly_balance,
                    "percentage_over": percentage_over
                },
                status="sent"
            )
            db.add(notification)
            db.commit()
        
        return sent
    
    async def send_upcoming_payments_alert(
        self,
        db: Session,
        user: User,
        upcoming_bills: List[Dict]
    ) -> bool:
        """Send alert for upcoming payments."""
        if not user.notif_prefs.get("email_enabled", True):
            return False
        
        if not upcoming_bills:
            return False
        
        total_amount = sum(bill.get("amount", 0) for bill in upcoming_bills)
        days_until = min(bill.get("days_until", 999) for bill in upcoming_bills)
        
        subject = f"📅 Você tem {len(upcoming_bills)} pagamento(s) próximo(s) - EconomizeIA"
        
        bills_html = ""
        for bill in upcoming_bills[:5]:  # Mostrar até 5 boletos
            days = bill.get("days_until", 0)
            bills_html += f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">
                    <p style="margin: 0 0 4px 0; color: #111827; font-size: 16px; font-weight: 600;">
                        {bill.get("issuer", "Desconhecido")}
                    </p>
                    <p style="margin: 0; color: #6b7280; font-size: 14px;">
                        R$ {bill.get("amount", 0):.2f} • Vence em {days} {('dia' if days == 1 else 'dias')}
                    </p>
                </td>
            </tr>
            """
        
        html_body = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f3f4f6; line-height: 1.6;">
            <table role="presentation" style="width: 100%; border-collapse: collapse; background-color: #f3f4f6; padding: 20px 0;">
                <tr>
                    <td align="center" style="padding: 40px 20px;">
                        <table role="presentation" style="max-width: 600px; width: 100%; border-collapse: collapse; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow: hidden;">
                            
                            <!-- Header -->
                            <tr>
                                <td style="background: linear-gradient(135deg, #f59e0b 0%, #f97316 100%); padding: 40px 40px; text-align: center;">
                                    <h1 style="margin: 0 0 8px 0; color: #ffffff; font-size: 32px; font-weight: 700; letter-spacing: -0.5px; line-height: 1.2;">
                                        📅 Pagamentos Próximos
                                    </h1>
                                    <p style="margin: 0; color: #fef3c7; font-size: 16px; font-weight: 400; line-height: 1.5;">
                                        EconomizeIA
                                    </p>
                                </td>
                            </tr>
                            
                            <!-- Content -->
                            <tr>
                                <td style="padding: 50px 40px;">
                                    <h2 style="margin: 0 0 20px 0; color: #111827; font-size: 24px; font-weight: 600; line-height: 1.3;">
                                        Olá, {user.name}!
                                    </h2>
                                    <p style="margin: 0 0 24px 0; color: #374151; font-size: 17px; line-height: 1.7;">
                                        Você tem <strong>{len(upcoming_bills)} pagamento(s)</strong> vencendo nos próximos dias.
                                    </p>
                                    
                                    <!-- Summary Card -->
                                    <div style="background-color: #fffbeb; border-radius: 10px; padding: 24px; margin-bottom: 24px; border-left: 4px solid #f59e0b;">
                                        <p style="margin: 0 0 12px 0; color: #78350f; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">
                                            Total a Pagar
                                        </p>
                                        <p style="margin: 0; color: #92400e; font-size: 32px; font-weight: 700; line-height: 1.4;">
                                            R$ {total_amount:.2f}
                                        </p>
                                        <p style="margin: 8px 0 0 0; color: #78350f; font-size: 14px;">
                                            Próximo vencimento em {days_until} {('dia' if days_until == 1 else 'dias')}
                                        </p>
                                    </div>
                                    
                                    <!-- Bills List -->
                                    <div style="background-color: #f9fafb; border-radius: 10px; padding: 20px; margin-bottom: 24px;">
                                        <p style="margin: 0 0 16px 0; color: #374151; font-size: 16px; font-weight: 600;">
                                            Boletos Pendentes:
                                        </p>
                                        <table role="presentation" style="width: 100%; border-collapse: collapse;">
                                            {bills_html}
                                        </table>
                                        {f'<p style="margin: 16px 0 0 0; color: #6b7280; font-size: 13px; text-align: center;">E mais {len(upcoming_bills) - 5} boleto(s)...</p>' if len(upcoming_bills) > 5 else ''}
                                    </div>
                                    
                                    <table role="presentation" style="width: 100%; border-collapse: collapse; margin-bottom: 24px;">
                                        <tr>
                                            <td align="center" style="padding: 0;">
                                                <a href="{settings.FRONTEND_URL or 'http://localhost:3000'}/bills" target="_blank" style="display: inline-block; padding: 14px 28px; background-color: #1f2937; color: #ffffff; font-size: 16px; font-weight: 600; text-decoration: none; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                                                    Ver Meus Boletos
                                                </a>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <p style="margin: 0; color: #4b5563; font-size: 16px; line-height: 1.7;">
                                        Não se esqueça de realizar os pagamentos para evitar juros e multas.
                                    </p>
                                </td>
                            </tr>
                            
                            <!-- Footer -->
                            <tr>
                                <td style="padding: 30px 40px; text-align: center; background-color: #f9fafb; border-top: 1px solid #e5e7eb;">
                                    <p style="margin: 0; color: #6b7280; font-size: 13px; line-height: 1.6;">
                                        © 2025 EconomizeIA. Todos os direitos reservados.
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
        
        text_body = f"""
Olá {user.name},

Você tem {len(upcoming_bills)} pagamento(s) vencendo nos próximos dias.

Total a Pagar: R$ {total_amount:.2f}
Próximo vencimento em {days_until} {('dia' if days_until == 1 else 'dias')}

Boletos Pendentes:
{chr(10).join([f"• {bill.get('issuer', 'Desconhecido')}: R$ {bill.get('amount', 0):.2f} (vence em {bill.get('days_until', 0)} dias)" for bill in upcoming_bills[:10]])}

Acesse seus boletos: {settings.FRONTEND_URL or 'http://localhost:3000'}/bills

Não se esqueça de realizar os pagamentos para evitar juros e multas.

Atenciosamente,
Equipe EconomizeIA
"""
        
        sent = await self.send_email(user.email, subject, text_body, html_body)
        
        if sent:
            # Log notification
            notification = Notification(
                id=uuid.uuid4(),
                user_id=user.id,
                type=NotificationType.REMINDER,
                channel=NotificationChannel.EMAIL,
                sent_at=datetime.utcnow(),
                payload={
                    "upcoming_bills_count": len(upcoming_bills),
                    "total_amount": total_amount,
                    "days_until": days_until,
                    "bills": upcoming_bills[:10]
                },
                status="sent"
            )
            db.add(notification)
            db.commit()
        
        return sent


notification_service = NotificationService()

