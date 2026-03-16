import smtplib
from email.message import EmailMessage


def send_excel(path):

    msg = EmailMessage()

    msg["Subject"] = "SUNAT Scraper Resultado"
    msg["From"] = "tu_email@gmail.com"
    msg["To"] = "gianmarcomejia@gmail.com"

    msg.set_content("Resultado del scraping.")

    with open(path, "rb") as f:

        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="correos.xlsx"
        )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:

        smtp.login("tu_email@gmail.com", "APP_PASSWORD")

        smtp.send_message(msg)