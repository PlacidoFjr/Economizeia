from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import timedelta, datetime, timezone
import logging
from app.db.database import get_db
from app.db.models import User
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    create_reset_token,
    create_verification_token,
    decode_token
)
from app.core.config import settings
from app.services.audit_service import audit_service
from app.services.notification_service import notification_service
from fastapi import Request

logger = logging.getLogger(__name__)

router = APIRouter()


class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: str = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class VerifyEmailRequest(BaseModel):
    token: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db),
    request: Request = None
):
    """Register a new user. Sends verification email."""
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        # Send informative email to user explaining the situation
        try:
            if not existing_user.email_verified:
                # If email not verified, offer to resend verification
                await notification_service.send_email_already_registered(existing_user, db, resend_verification=True)
            else:
                # If email verified, just inform and offer login
                await notification_service.send_email_already_registered(existing_user, db, resend_verification=False)
        except Exception as e:
            logger.warning(f"Failed to send 'email already registered' notification to {user_data.email}: {e}")
            # Continue anyway - don't fail the request if email fails
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado"
        )
    
    # Create user (email not verified yet)
    user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        phone=user_data.phone,
        email_verified=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Generate verification token
    verification_token = create_verification_token(data={"sub": str(user.id), "email": user.email})
    verification_token_expires = datetime.now(timezone.utc) + timedelta(hours=24)
    
    # Save verification token
    user.verification_token = verification_token
    user.verification_token_expires = verification_token_expires
    db.commit()
    
    # Audit log
    audit_service.log_action(
        db=db,
        entity="user",
        action="create",
        user_id=user.id,
        details={"email": user.email},
        request=request
    )
    
    # Send verification email
    try:
        await notification_service.send_verification_email(user, verification_token)
    except Exception as e:
        logger.warning(f"Failed to send verification email to {user.email}: {e}")
        # Don't fail registration if email fails
    
    return {
        "message": "Conta criada com sucesso! Verifique seu email para confirmar o registro.",
        "email": user.email,
        "requires_verification": True
    }


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: Session = Depends(get_db),
    request: Request = None
):
    """Login and get JWT tokens."""
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta de usuário inativa"
        )
    
    # Check if email is verified
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email não verificado. Verifique seu email e clique no link de confirmação."
        )
    
    # Audit log
    audit_service.log_action(
        db=db,
        entity="user",
        action="login",
        user_id=user.id,
        request=request
    )
    
    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""
    payload = decode_token(token_data.refresh_token)
    
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de atualização inválido"
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou inativo"
        )
    
    # Generate new tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/forgot-password")
async def forgot_password(
    request_data: ForgotPasswordRequest,
    db: Session = Depends(get_db),
    request: Request = None
):
    """Request password reset. Sends email with reset link."""
    user = db.query(User).filter(User.email == request_data.email).first()
    
    # Always return success to prevent email enumeration
    if not user:
        return {"message": "Se o email existir, um link de redefinição será enviado."}
    
    # Generate reset token
    reset_token = create_reset_token(data={"sub": str(user.id), "email": user.email})
    reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    
    # Save token to user
    user.reset_token = reset_token
    user.reset_token_expires = reset_token_expires
    db.commit()
    
    # Send email with reset link
    reset_link = f"{settings.FRONTEND_URL or 'http://localhost:3000'}/reset-password?token={reset_token}"
    
    email_subject = "Redefinição de Senha - EconomizeIA"
    email_body = f"""
Olá {user.name},

Você solicitou a redefinição de senha da sua conta EconomizeIA.

Clique no link abaixo para redefinir sua senha (válido por 1 hora):
{reset_link}

Se você não solicitou esta redefinição, ignore este email.

Atenciosamente,
Equipe EconomizeIA
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
                            <td style="background: linear-gradient(135deg, #1f2937 0%, #374151 100%); padding: 40px 40px; text-align: center;">
                                <h1 style="margin: 0 0 8px 0; color: #ffffff; font-size: 32px; font-weight: 700; letter-spacing: -0.5px; line-height: 1.2;">
                                    EconomizeIA
                                </h1>
                                <p style="margin: 0; color: #e5e7eb; font-size: 16px; font-weight: 400; line-height: 1.5;">
                                    Redefinição de Senha
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding: 50px 40px;">
                                <h2 style="margin: 0 0 20px 0; color: #111827; font-size: 24px; font-weight: 600; line-height: 1.3;">
                                    Olá, {user.name}!
                                </h2>
                                <p style="margin: 0 0 20px 0; color: #374151; font-size: 17px; line-height: 1.7;">
                                    Você solicitou a redefinição de senha da sua conta <strong style="color: #1f2937;">EconomizeIA</strong>.
                                </p>
                                <p style="margin: 0 0 32px 0; color: #4b5563; font-size: 16px; line-height: 1.7;">
                                    Clique no botão abaixo para criar uma nova senha. Este link é válido por <strong style="color: #1f2937;">1 hora</strong>.
                                </p>
                                
                                <!-- CTA Button -->
                                <table role="presentation" style="width: 100%; border-collapse: collapse; margin-bottom: 32px;">
                                    <tr>
                                        <td align="center">
                                            <a href="{reset_link}" style="display: inline-block; padding: 16px 40px; background-color: #1f2937; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 17px; line-height: 1.5;">
                                                Redefinir Minha Senha →
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- Alternative Link -->
                                <div style="background-color: #f9fafb; border-radius: 8px; padding: 20px; margin-bottom: 24px; border-left: 4px solid #3b82f6;">
                                    <p style="margin: 0 0 12px 0; color: #374151; font-size: 14px; font-weight: 600; line-height: 1.6;">
                                        Não consegue clicar no botão?
                                    </p>
                                    <p style="margin: 0; color: #6b7280; font-size: 13px; line-height: 1.6; word-break: break-all;">
                                        Copie e cole este link no seu navegador:<br>
                                        <span style="color: #3b82f6;">{reset_link}</span>
                                    </p>
                                </div>
                                
                                <!-- Security Notice -->
                                <div style="background-color: #fef3c7; border-radius: 8px; padding: 16px; border-left: 4px solid #f59e0b;">
                                    <p style="margin: 0; color: #92400e; font-size: 14px; line-height: 1.6;">
                                        <strong>⚠️ Importante:</strong> Se você não solicitou esta redefinição, ignore este email. Sua senha permanecerá inalterada.
                                    </p>
                                </div>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="padding: 40px; text-align: center; background-color: #f9fafb; border-top: 2px solid #e5e7eb;">
                                <p style="margin: 0 0 12px 0; color: #374151; font-size: 15px; line-height: 1.6;">
                                    <strong style="color: #111827;">Precisa de ajuda?</strong>
                                </p>
                                <p style="margin: 0 0 20px 0; color: #6b7280; font-size: 14px; line-height: 1.6;">
                                    Se você tiver alguma dúvida, entre em contato conosco.
                                </p>
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
    
    # Try to send email
    email_sent = await notification_service.send_email(
        to=user.email,
        subject=email_subject,
        body=email_body,
        html_body=html_body
    )
    
    if email_sent:
        logger.info(f"Password reset email sent successfully to {user.email}")
    else:
        # If email not configured, log the token (for development)
        logger.warning(f"SMTP not configured. Reset token for {user.email}: {reset_token}")
        logger.warning(f"Reset link: {reset_link}")
    
    # Audit log
    audit_service.log_action(
        db=db,
        entity="user",
        action="password_reset_requested",
        user_id=user.id,
        details={"email": user.email},
        request=request
    )
    
    return {"message": "Se o email existir, um link de redefinição será enviado."}


@router.post("/reset-password")
async def reset_password(
    reset_data: ResetPasswordRequest,
    db: Session = Depends(get_db),
    request: Request = None
):
    """Reset password using reset token."""
    # Decode token
    payload = decode_token(reset_data.token)
    
    if payload is None or payload.get("type") != "reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido ou expirado"
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Verify token matches stored token and is not expired
    if user.reset_token != reset_data.token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido"
        )
    
    if not user.reset_token_expires or user.reset_token_expires < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token expirado. Solicite um novo link de redefinição."
        )
    
    # Validate password strength
    if len(reset_data.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A senha deve ter pelo menos 6 caracteres"
        )
    
    # Update password
    user.password_hash = get_password_hash(reset_data.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()
    
    # Audit log
    audit_service.log_action(
        db=db,
        entity="user",
        action="password_reset",
        user_id=user.id,
        details={"email": user.email},
        request=request
    )
    
    return {"message": "Senha redefinida com sucesso"}


@router.post("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(
    verify_data: VerifyEmailRequest,
    db: Session = Depends(get_db),
    request: Request = None
):
    """Verify user email using verification token."""
    payload = decode_token(verify_data.token)
    
    if payload is None or payload.get("type") != "verification":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido ou expirado"
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Verify token matches stored token and is not expired
    if user.verification_token != verify_data.token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido"
        )
    
    if not user.verification_token_expires or user.verification_token_expires < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token expirado. Solicite um novo link de verificação."
        )
    
    # Mark email as verified
    user.email_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    db.commit()
    
    # Audit log
    audit_service.log_action(
        db=db,
        entity="user",
        action="email_verified",
        user_id=user.id,
        details={"email": user.email},
        request=request
    )
    
    # Send welcome email after verification
    try:
        await notification_service.send_welcome_email(user)
    except Exception as e:
        logger.warning(f"Failed to send welcome email to {user.email}: {e}")
    
    return {"message": "Email verificado com sucesso! Você já pode fazer login."}


@router.post("/resend-verification", status_code=status.HTTP_200_OK)
async def resend_verification(
    request_data: ForgotPasswordRequest,  # Reuse same model (just needs email)
    db: Session = Depends(get_db),
    request: Request = None
):
    """Resend verification email."""
    user = db.query(User).filter(User.email == request_data.email).first()
    
    if not user:
        # Return generic response to prevent email enumeration
        return {"message": "Se o email existir e não estiver verificado, um novo link será enviado."}
    
    if user.email_verified:
        return {"message": "Este email já foi verificado. Você pode fazer login normalmente."}
    
    # Generate new verification token
    verification_token = create_verification_token(data={"sub": str(user.id), "email": user.email})
    verification_token_expires = datetime.now(timezone.utc) + timedelta(hours=24)
    
    # Save verification token
    user.verification_token = verification_token
    user.verification_token_expires = verification_token_expires
    db.commit()
    
    # Send verification email
    try:
        await notification_service.send_verification_email(user, verification_token)
        logger.info(f"Verification email resent to {user.email}")
    except Exception as e:
        logger.error(f"Failed to resend verification email to {user.email}: {e}")
    
    return {"message": "Se o email existir e não estiver verificado, um novo link será enviado."}

