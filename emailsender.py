import yagmail
def send_email(to, subject, body):
    # 发件人和收件人信息
    sender_email = "3348536459@qq.com"
    receiver_email = to
    password = "juucpqkdrkglcjab"  # 使用授权码代替密码

    yag = yagmail.SMTP(sender_email, password, host="smtp.qq.com", port=465, smtp_ssl=True)

    subject = subject
    contents = body
    yag.send(receiver_email, subject, contents)

    print("邮件已发送成功！")

if __name__ == '__main__':
    send_email("3348536459@qq.com","这是main函数调用","降价提醒示例")