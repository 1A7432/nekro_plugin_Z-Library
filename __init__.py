import httpx
from nekro_agent.api.schemas import AgentCtx
from nekro_agent.core import logger
from nekro_agent.services.plugin.base import ConfigBase, NekroPlugin, SandboxMethodType
from pydantic import Field

logger.info("正在加载 Z-Library 搜索插件 (nekro_plugin_zlibrary)...")

# 1. 插件元信息
plugin = NekroPlugin(
    name="Z-Library 图书搜索",
    module_name="nekro_plugin_zlibrary",
    description="通过 Z-Library API 搜索图书并获取下载链接。",
    version="1.0.0",
    author="dirac",
    url="https://github.com/1A7432/nekro_plugin_Z-Library",
)


# 2. 插件配置
@plugin.mount_config()
class ZLibConfig(ConfigBase):
    """Z-Library 插件配置"""

    API_DOMAIN: str = Field(
        default="zh.zlibc.ru",
        title="Z-Library API 域名",
        description="用于 API 请求的基础域名。如果官方域名变更，可在此处修改。",
    )
    REMIX_USERID: str = Field(
        default="",
        title="Z-Library Remix User ID",
        description="登录 Z-Library 网站后，从浏览器 Cookie 获取的 `remix_userid`。",
    )
    REMIX_USERKEY: str = Field(
        default="",
        title="Z-Library Remix User Key",
        description="登录 Z-Library 网站后，从浏览器 Cookie 获取的 `remix_userkey`。",
    )


# 3. 获取配置实例
config: ZLibConfig = plugin.get_config(ZLibConfig)


# 4. 核心功能：搜索图书
@plugin.mount_sandbox_method(SandboxMethodType.AGENT, name="搜索图书", description="根据关键词搜索 Z-Library 图书")
async def book_search(ctx: AgentCtx, query: str) -> str:
    """根据关键词搜索 Z-Library 图书，并返回格式化的结果列表。"""
    if not config.REMIX_USERID or not config.REMIX_USERKEY:
        return "插件配置不完整，请在插件设置中填写 REMIX_USERID 和 REMIX_USERKEY。"

    api_url = f"https://{config.API_DOMAIN}/eapi/book/search"
    headers = {"User-Agent": "Nekro-Agent-ZLib-Plugin/1.0"}
    cookies = {"remix_userid": config.REMIX_USERID, "remix_userkey": config.REMIX_USERKEY}
    # API 要求 message 参数必须存在
    params = {"message": query, "limit": 10, "page": 1}

    logger.info(f"开始使用 Z-Library 搜索: {query}")

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.get(api_url, headers=headers, cookies=cookies, params=params)
            response.raise_for_status()
        
        data = response.json()
        if not data.get("success") or not data.get("books"):
            return f"未能找到与“{query}”相关的结果，或 API 返回错误。"

        books = data["books"]
        if not books:
            return f"未能找到与“{query}”相关的结果。"

        result_parts = [f"为您找到关于“{query}”的相关图书 {len(books)} 本:\n"]
        for i, book in enumerate(books, 1):
            # 提取关键信息
            title = book.get("title", "无标题")
            author = book.get("author", "未知作者")
            year = book.get("year", "未知年份")
            extension = book.get("extension", "未知格式")
            book_id = book.get("id")
            book_hash = book.get("hash")
            
            # 格式化单条结果
            result_parts.append(
                f"{i}. {title}\n"
                f"   作者: {author} | 年份: {year} | 格式: {extension}\n"
                f"   下载指令: /exec get_download_link(book_id='{book_id}', book_hash='{book_hash}')"
            )

        return "\n".join(result_parts)

    except httpx.HTTPStatusError as e:
        logger.error(f"调用 Z-Lib API 时发生 HTTP 错误: {e.response.status_code}")
        return f"搜索服务请求失败，状态码: {e.response.status_code}。请检查您的网络或配置。"
    except Exception as e:
        logger.error(f"Z-Lib 搜索时发生未知错误: {e}")
        return f"搜索时遇到未知错误: {e}"


# 5. 核心功能：获取下载链接
@plugin.mount_sandbox_method(SandboxMethodType.AGENT, name="获取下载链接", description="获取指定图书的下载链接")
async def get_download_link(ctx: AgentCtx, book_id: str, book_hash: str) -> str:
    """根据 book_id 和 book_hash 获取图书的临时下载链接。"""
    if not config.REMIX_USERID or not config.REMIX_USERKEY:
        return "插件配置不完整，请在插件设置中填写 REMIX_USERID 和 REMIX_USERKEY。"

    api_url = f"https://{config.API_DOMAIN}/eapi/book/{book_id}/{book_hash}/file"
    headers = {"User-Agent": "Nekro-Agent-ZLib-Plugin/1.0"}
    cookies = {"remix_userid": config.REMIX_USERID, "remix_userkey": config.REMIX_USERKEY}

    logger.info(f"正在为 book_id={book_id} 获取下载链接...")

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.get(api_url, headers=headers, cookies=cookies)
            response.raise_for_status()

        data = response.json()
        if data.get("success") and data.get("file"):
            download_url = data["file"].get("downloadLink")
            if download_url:
                logger.info(f"成功获取下载链接: {download_url}")
                return f"已成功获取下载链接，请点击访问：{download_url}"
            else:
                return "API 未返回有效的下载链接。"
        else:
            return f"获取下载链接失败: {data.get('message', '未知 API 错误')}"

    except httpx.HTTPStatusError as e:
        logger.error(f"获取下载链接时发生 HTTP 错误: {e.response.status_code}")
        return f"获取下载链接失败，状态码: {e.response.status_code}。可能是下载次数已达上限。"
    except Exception as e:
        logger.error(f"获取下载链接时发生未知错误: {e}")
        return f"获取下载链接时遇到未知错误: {e}"
