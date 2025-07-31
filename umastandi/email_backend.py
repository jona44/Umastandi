import ssl
import smtplib
from django.core.mail.backends.smtp import EmailBackend


class UnsafeEmailBackend(EmailBackend):
    def open(self):
        if self.connection:
            return False

        connection_class = smtplib.SMTP_SSL if self.use_ssl else smtplib.SMTP

        try:
            self.connection = connection_class(
                self.host, self.port, timeout=self.timeout # type: ignore
            )

            if self.use_tls:
                context = ssl._create_unverified_context()
                self.connection.starttls(context=context)

            if self.username and self.password:
                self.connection.login(self.username, self.password)

            return True

        except Exception as e:
            if not self.fail_silently:
                raise e
            return False
