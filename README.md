# Nekro Z-Library 图书搜索插件

这是一个为 Nekro Agent 开发的插件，通过调用非官方的 Z-Library API 实现图书搜索和下载链接获取功能。

## 功能特性

- **强大的图书搜索**：利用 Z-Library 的庞大书库，通过关键词搜索书籍。
- **两步式下载**：先搜索获取书籍列表，再根据指定书籍获取临时下载链接，流程清晰。
- **用户认证**：通过用户自己的 `UserID` 和 `UserKey` 进行认证，以访问其账户对应的下载额度。

## 配置

要在 Nekro Agent 中使用此插件，您需要获取并填入以下三项信息：

1.  **API_DOMAIN**: Z-Library 的 API 域名。通常默认为 `zh.zlibc.ru`，一般无需修改，除非域名失效。
2.  **REMIX_USERID**: 您的用户 ID。
3.  **REMIX_USERKEY**: 您的用户密钥。

### 如何获取 `REMIX_USERID` 和 `REMIX_USERKEY`？

1.  使用您的浏览器登录 Z-Library 网站。
2.  登录成功后，按 `F12` 打开“开发者工具”。
3.  切换到 “Application”（应用）或“存储”（Storage）标签页。
4.  在左侧菜单中，找到 “Cookies” 选项，并点击对应的 Z-Library 域名。
5.  在右侧的 Cookie 列表中，找到名为 `remix_userid` 和 `remix_userkey` 的条目，复制它们对应的 `Value`（值），并填入插件配置中。

**注意：请妥善保管您的 UserID 和 UserKey，不要泄露给他人。**

## 使用方法

插件提供两个核心功能：

### 1. 搜索图书

使用 `/exec` 指令调用 `book_search` 函数。它会返回一个包含书名、作者、格式和下载指令的列表。

**示例：**
```
/exec book_search(query="python crash course")
```

**返回结果可能如下：**
```
为您找到关于“python crash course”的相关图书 10 本:

1. Python Crash Course, 2nd Edition
   作者: Eric Matthes | 年份: 2019 | 格式: pdf
   下载指令: /exec get_download_link(book_id='12345', book_hash='abcde')

2. Python Crash Course
   作者: Eric Matthes | 年份: 2016 | 格式: epub
   下载指令: /exec nekro_plugin_zlibrary.get_download_link(book_id='67890', book_hash='fghij')
```

### 2. 获取下载链接

从上面的搜索结果中，复制您想下载的书籍对应的**完整下载指令**，并发送给 Agent。

**示例：**
```
/exec get_download_link(book_id='12345', book_hash='abcde')
```

插件会返回一个有时效性的直接下载链接，点击即可下载。

## 注意事项

- 本插件依赖非官方 API，其可用性无法得到保证。
- Z-Library 对每日下载数量有限制。如果获取链接失败，可能是因为您已达到当天的下载上限。
