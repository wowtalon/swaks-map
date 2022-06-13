#!/usr/bin/python3
# -*- coding: UTF8 -*-

import argparse
import os
import tempfile
import src.swaks as swaks
from base64 import b64encode
from getpass import getuser
from time import sleep
from socket import gethostname
from validate_email import validate_email
from src.utils import *


def send_mail(mail_to, args):
    '''
    调用 Swaks 发送邮件

    mail_to: 收件人邮箱
    '''
    tf = tempfile.NamedTemporaryFile()
    # 构造发送邮件的参数
    resp = swaks.send_mail(mail_to, args)
    tf.close()
    ret = parse_result(resp)
    if ret is True:
        echo_ok(f'发送到 {mail_to} 成功')
    else:
        echo_error(f'发送到 {mail_to} 失败\n[x] {ret}')
    return resp


def send_mail_by_line(line, args):
    '''
    从文件读取收件人和发件人，逐行发送邮件
    line: 从文件读取的一行
    args: ArgumentParser.parse_args()

    line支持几种格式：
    1. mail_to
    2. mail_from,mail_to
    3. au,ap,server,mail_from,mail_to
    '''
    orig_au = args.au
    orig_ap = args.ap
    orig_server = args.server
    orig_from = args.mail_from
    line = line.replace('\n', '')
    comma_count = line.count(',')
    if comma_count == 0:
        resp = send_mail(line, args)
    if comma_count == 1:
        mail_from, mail_to = line.split(',')
        args.mail_from = mail_from
        resp = send_mail(mail_to, args)
    if comma_count == 4:
        au, ap, server, mail_from, mail_to = line.split(',')
        args.au = au
        args.ap = ap
        args.server = server
        args.mail_from = mail_from
        resp = send_mail(mail_to, args)
    # 重置
    args.au = orig_au
    args.ap = orig_ap
    args.server = orig_server
    args.mail_from = orig_from
    return resp


def preset_args(args):
    '''
    预处理 args
    '''
    header = {}
    for _header in args.header:
        h_key, h_val = _header.split(': ')
        header[h_key] = h_val
    args.header = header
    if 'To' not in args.header and len(args.header['To']) == 0:
        args.header['To'] = []
        for mail_to in args.to:
            to_user = mail_to.split('@')[0]
            args.header['To'].append(f'{to_user} <{mail_to}>')
        args.header['To'] = ','.join(args.header['To'])
    if args.cc:
        h_cc = []
        for cc in args.cc:
            cc_user = cc.split('@')[0]
            h_cc.append(f'{cc_user} <{cc}>')
        args.header['Cc'] = ','.join(h_cc)
        args.to.extend(args.cc)
    if args.subject and not args.eml:
        subject_b64 = b64encode(args.subject.encode('utf-8')).decode('utf-8')
        args.header['Subject'] = f'=?UTF-8?B?{subject_b64}?='
    username = getuser()
    hostname = gethostname()
    if not args.mail_from:
        args.mail_from = f'{username}@{hostname}'
    if not args.fnickname:
        args.fnickname = username
    args.header['From'] = f'{args.fnickname} <{args.mail_from}>'
    args.header['X-Mailer'] = 'Swaks Map v0.1 github.com/wowtalon/swaks-map/'
    return args


def run(args):
    '''
    入口函数
    '''
    with open(args.output, 'a+') as output_file:
        # 从文件读取收件人
        if args.file:
            if not os.path.isfile(args.file):
                echo_error( f'File invalid: {args.file}', exit_now=True)
            else:
                with open(args.file, 'r') as email_file:
                    for line in email_file:
                        if args.delay > 0:
                            sleep(args.delay)
                        resp = send_mail_by_line(line, args)
                        output_file.write(resp)
        # 逐个账号发送邮件
        if args.to:
            for email in args.to:
                if args.delay > 0:
                    sleep(args.delay)
                if validate_email(email):
                    resp = send_mail(email, args)
                    output_file.write(resp)
                else:
                    echo_error(f'Email invalid: {email}', exit_now=True)


if __name__ == '__main__':
    banner = '''
   _____               __              __  ___          
  / ___/      ______ _/ /_______      /  |/  /___ _____ 
  \__ \ | /| / / __ `/ //_/ ___/_____/ /|_/ / __ `/ __ \\
 ___/ / |/ |/ / /_/ / ,< (__  )_____/ /  / / /_/ / /_/ /
/____/|__/|__/\__,_/_/|_/____/     /_/  /_/\__,_/ .___/ 
                                               /_/ 
V0.1 By wowtalon(https://github.com/wowtalon/swaks-map)
'''
    print(banner)
    parser = argparse.ArgumentParser()
    mail_group = parser.add_argument_group('邮件配置')
    mail_group.add_argument('--mail-from', help='指定发件人的邮箱账号')
    mail_group.add_argument('--fnickname', help='指定发件人的别名，会显示在邮件发件人上，需要制定了发件人账号时才有效。')
    mail_group.add_argument('--to', help='指定邮件接收人的邮箱账号或包含多个邮箱账号的文件', action='append')
    mail_group.add_argument('--file', help='从文件指定发件人和收件人，一行一个')
    mail_group.add_argument('--cc', help='指定抄送目标', action='append')
    mail_group.add_argument('--header', help='指定邮件header', action='append')
    mail_group.add_argument('--body', help='指定想要发送的邮件内容', default='Hello, World!')
    mail_group.add_argument('--subject', help='指定想要发送的邮件标题', default='Test Mail From Swaks-Map')
    mail_group.add_argument('--attach', help='指定想要发送的附件，如--attach test.zip', action='append')
    eml_group = parser.add_argument_group('邮件模板配置')
    eml_group.add_argument('--eml', help='指定想要发送的EML文件')
    eml_group.add_argument('--html', help='指定想要发送的HTML模板')
    eml_group.add_argument('--vars', help='指定HTML模板中的变量，格式为key=val，如--vars \'name=张三\'', action='append')
    smtp_group = parser.add_argument_group('SMTP配置')
    smtp_group.add_argument('--server', help='指定SMTP服务器')
    smtp_group.add_argument('--au', help='指定SMTP账号')
    smtp_group.add_argument('--ap', help='指定SMTP密码')
    output_group = parser.add_argument_group('输出配置')
    output_group.add_argument('--output', help='指定输出结果文件名', default='result.txt')
    misc_group = parser.add_argument_group('其他配置')
    misc_group.add_argument('--delay', help='指定发送时间间隔，单位：秒，默认值为1', type=int, default=1)
    args = parser.parse_args()
    if not (args.file or args.to):
        echo_error('Email not indicated, please indicate by --to or --file.', exit_now=True)
    args = preset_args(args)
    run(args)
