# Swaks-Map

---

<img src="https://img.shields.io/badge/python-v3.7-blue" />

<pre>
   _____               __              __  ___          
  / ___/      ______ _/ /_______      /  |/  /___ _____ 
  \__ \ | /| / / __ `/ //_/ ___/_____/ /|_/ / __ `/ __ \
 ___/ / |/ |/ / /_/ / ,< (__  )_____/ /  / / /_/ / /_/ /
/____/|__/|__/\__,_/_/|_/____/     /_/  /_/\__,_/ .___/ 
                                               /_/ 
</pre>

## 介绍

调用 [Swaks](https://github.com/jetmore/swaks) 实现批量发送邮件，此外还基于 [JinJa2](https://jinja.palletsprojects.com/) 实现了 HTML 邮件模板。支持：

+ 批量邮件发送，并且支持自定义发送时间间隔

+ 使用指定账号登录 SMTP 服务器发送邮件

+ 指定 EML 文件发送

+ 使用 HTML 文件作为邮件模板，通过命令行指定参数注入到 HTML 模板中，实现动态邮件内容

## 快速开始

```bash
git clone https://github.com/wowtalon/swaks-map.git

cd swaks-map

pip install -r requirements.txt

python swaks-map.py -h

python swaks-map.py --to xxxx@qq.com
```

![](assets/help.gif)

## 命令示例

### 发送单封邮件

```bash
python swaks-map.py --to wowtalon@gmail.com
```

![](assets/sendok.png)

### 批量发送

```bash
python swaks-map.py --to emails.txt
```

### 登录 SMTP 发送

```bash
python swaks-map.py --to emails.txt --server smtp.163.com \
 --au xxxx@163.com --ap xxx \
 --mail-from xxxx@163.com
```

### HTML 模板发送

```html
<!-- test.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
</head>
<body>
    <h1>你好，{{ name }}</h1><!-- 通过命令行指定的变量 -->
    <p>{{ date }}</p><!-- 内置变量 -->
    <p>{{ time }}</p><!-- 内置变量 -->
    <p>{{ datetime }}</p><!-- 内置变量 -->
    <p>{{ mail_to }}</p><!-- 内置变量 -->
</body>
</html>
```

```bash
python swaks-map.py --to wowtalon@gmail.com \
 --html test.html --vars "name=Talon"
```

![](assets/html.png)

收件截图：

![](assets/html-mail.png)

### EML 邮件发送

可以从邮箱导出 EML 文件，并且指定该 EML 文件进行发送，`swaks-map` 会自动提取 EML 中的邮件标题、附件、正文进行发送。

```bash
python swaks-map.py --to xxx@qq.com --eml ./example.eml
```

### 发送附件

```bash
python swaks-map.py --to xxx@qq.com --attach ./test.txt
```

### 发送多个附件

```bash
python swaks-map.py --to xxx@qq.com --attach ./test.docx \
 --attach a.pdf
```

## 参数说明

### 邮件参数

#### --mail-from

用于指定发送邮箱，会显示在邮件的发件人处。

```bash
python swaks-map.py --mail-from admin@abctest.com
```

#### --fnickname

用于指定发送人的名称，会显示在邮件的发件人处。

```bash
python swaks-map.py --fnickname '管理员'
```

#### --to

用于指定收件人，可以指定多个。

```bash
python swaks-map.py --to user1@test.com --to user2@test.com
```

#### --file

用于指定收件人列表，参数是一个文件名。

```
# email.txt
user1@test.com
user2@test.com
...
userxx@test.com
```

```bash
python swaks-map.py --file email.txt
```

#### --cc

用于指定抄送人。

```bash
python swaks-map.py --to 123@test.com --cc cc_user1@test.com \
 --cc cc_user2@test.com ...
```

#### --header

用于指定邮件头。

#### --body

用于指定邮件正文。

```bash
python swaks-map.py --to xxx@test.com --body 'This is the body.' ...
```

#### --subject

用于指定邮件标题。

```bash
python swaks-map.py --to xxx@test.com --subject 'This is the title' ...
```

#### --attach

用于指定附件。

```bash
python swaks-map.py --to xxx@test.com --attach /path/to/attach1 \
 --attach /path/to/attach2 ...
```

### 邮件模板配置

#### --eml

用于指定 EML 文件进行发送。

```bash
python swaks-map.py --to xxx@test.com --eml /path/to/emlfile ...
```

#### --html

用于指定 HTML 模板。

HTML 模板：

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document</title>
</head>
<body>
    {{ to_user }}
    {{ to_domain }}
    {{ mail_to }}
    {{ date }}
    {{ time }}
    {{ datetime }}
    {{ var1 }}
</body>
</html>
```

```bash
python swaks-map.py --to xxx@test.com --html /path/to/htmlfile
```

#### --vars

配合 `--html` 使用，用于向 HTML 文件注入参数。

```bash
python swaks-map.py --to xxx@test.com --html /path/to/htmlfile \
 --vars 'varname=varvalue'
```

### SMTP配置

#### --server

用于指定要登录的 SMTP 服务器，如 `smtp.qq.com`。

#### --au

用于指定登录 SMTP 服务器用的用户名。

#### --ap

用于指定登录 SMTP 服务器用的用户密码。

### 输出配置

#### --output

用于指定输出文件。

### 其他配置

#### --delay

用于指定多封邮件之间的间隔，单位：秒。
