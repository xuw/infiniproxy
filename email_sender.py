"""Email notification service for API key distribution."""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import Optional
import os

logger = logging.getLogger(__name__)


class EmailSender:
    """Sends email notifications for API keys."""

    def __init__(self):
        """Initialize email sender with SMTP configuration."""
        # SMTP Configuration from environment or defaults
        self.smtp_server = os.getenv("SMTP_SERVER", "mail.tsinghua.edu.cn")
        self.smtp_port = int(os.getenv("SMTP_PORT", "465"))
        self.smtp_user = os.getenv("SMTP_USER", "weixu@tsinghua.edu.cn")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "r4bBkYZ28Y943awR")
        self.use_ssl = os.getenv("SMTP_USE_SSL", "true").lower() == "true"

        logger.info(f"Email sender initialized: {self.smtp_server}:{self.smtp_port} (SSL: {self.use_ssl})")

    def _create_api_key_email(self, username: str, email: str, api_key: str) -> MIMEMultipart:
        """
        Create an email message with API key information in Chinese.

        Args:
            username: User's username
            email: User's email address
            api_key: API key to send

        Returns:
            MIMEMultipart email message
        """
        msg = MIMEMultipart('alternative')
        msg['From'] = Header(f"InfiniProxy 系统 <{self.smtp_user}>", 'utf-8')
        msg['To'] = Header(email, 'utf-8')
        msg['Subject'] = Header('您的 InfiniProxy API 密钥', 'utf-8')

        # Plain text version
        text_content = f"""
您好 {username}，

您的 InfiniProxy API 密钥已经创建成功。

API 密钥: {api_key}

重要提示：
1. 请妥善保管此密钥，不要与他人分享
2. 此密钥只会显示一次，请立即保存
3. 如果密钥丢失，请联系管理员重新生成

使用方法：

1. API 请求方式
在您的 API 请求中添加以下 Header：
Authorization: Bearer {api_key}

服务地址：
- OpenAI 格式: https://aiapi.iiis.co:9443/v1/chat/completions
- Claude 格式: https://aiapi.iiis.co:9443/v1/messages

2. Claude Code 配置方式
在终端中执行以下命令配置 Claude Code：

export ANTHROPIC_AUTH_TOKEN={api_key}
export ANTHROPIC_BASE_URL=https://aiapi.iiis.co:9443
claude

提示：将上述 export 命令添加到 ~/.bashrc 或 ~/.zshrc 以永久生效。

如有任何问题，请联系管理员。

祝您使用愉快！

---
InfiniProxy 系统
此邮件由系统自动发送，请勿回复
"""

        # HTML version
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
        .content {{ background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
        .api-key {{ background-color: #fff; padding: 15px; border-left: 4px solid #4CAF50; margin: 15px 0; font-family: 'Courier New', monospace; word-break: break-all; }}
        .warning {{ background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 15px 0; }}
        .info {{ background-color: #d1ecf1; border-left: 4px solid #0c5460; padding: 15px; margin: 15px 0; }}
        .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        h2 {{ color: #4CAF50; }}
        code {{ background-color: #f4f4f4; padding: 2px 6px; border-radius: 3px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>InfiniProxy API 密钥</h1>
        </div>
        <div class="content">
            <p>您好 <strong>{username}</strong>，</p>

            <p>您的 InfiniProxy API 密钥已经创建成功。</p>

            <div class="api-key">
                <strong>API 密钥：</strong><br>
                <code>{api_key}</code>
            </div>

            <div class="warning">
                <strong>⚠️ 重要提示：</strong>
                <ul>
                    <li>请妥善保管此密钥，不要与他人分享</li>
                    <li>此密钥只会显示一次，请立即保存</li>
                    <li>如果密钥丢失，请联系管理员重新生成</li>
                </ul>
            </div>

            <div class="info">
                <h2>使用方法</h2>

                <h3>1. API 请求方式</h3>
                <p>在您的 API 请求中添加以下 Header：</p>
                <code>Authorization: Bearer {api_key}</code>

                <h4>服务地址</h4>
                <ul>
                    <li><strong>OpenAI 格式：</strong> <code>https://aiapi.iiis.co:9443/v1/chat/completions</code></li>
                    <li><strong>Claude 格式：</strong> <code>https://aiapi.iiis.co:9443/v1/messages</code></li>
                </ul>

                <h3>2. Claude Code 配置方式</h3>
                <p>在终端中执行以下命令配置 Claude Code：</p>
                <pre style="background-color: #2d3748; color: #e2e8f0; padding: 15px; border-radius: 5px; overflow-x: auto;">export ANTHROPIC_AUTH_TOKEN={api_key}
export ANTHROPIC_BASE_URL=https://aiapi.iiis.co:9443
claude</pre>
                <p><strong>提示：</strong>将上述 export 命令添加到 <code>~/.bashrc</code> 或 <code>~/.zshrc</code> 以永久生效。</p>
            </div>

            <p>如有任何问题，请联系管理员。</p>
            <p>祝您使用愉快！</p>
        </div>
        <div class="footer">
            <p>InfiniProxy 系统<br>此邮件由系统自动发送，请勿回复</p>
        </div>
    </div>
</body>
</html>
"""

        # Attach both plain text and HTML versions
        part1 = MIMEText(text_content, 'plain', 'utf-8')
        part2 = MIMEText(html_content, 'html', 'utf-8')

        msg.attach(part1)
        msg.attach(part2)

        return msg

    def send_api_key_email(self, username: str, email: str, api_key: str) -> bool:
        """
        Send API key to user's email address.

        Args:
            username: User's username
            email: User's email address
            api_key: API key to send

        Returns:
            True if email sent successfully, False otherwise
        """
        if not email:
            logger.warning(f"No email address provided for user {username}")
            return False

        try:
            # Create email message
            msg = self._create_api_key_email(username, email, api_key)

            # Send email
            if self.use_ssl:
                # Use SSL connection (port 465)
                logger.info(f"Connecting to SMTP server {self.smtp_server}:{self.smtp_port} with SSL")
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=10) as server:
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            else:
                # Use TLS connection (port 25 or 587)
                logger.info(f"Connecting to SMTP server {self.smtp_server}:{self.smtp_port} with TLS")
                with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)

            logger.info(f"✅ API key email sent successfully to {email}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ SMTP authentication failed: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"❌ SMTP error sending email to {email}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error sending email to {email}: {e}")
            return False
