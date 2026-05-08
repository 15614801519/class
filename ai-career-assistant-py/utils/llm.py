import os
import sys
import json
import requests
from openai import OpenAI
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 获取火山方舟 API 配置
ARK_API_KEY = os.getenv("ARK_API_KEY")
MODEL = os.getenv("ARK_MODEL", "ep-20260428162855-c4fpp")  # 默认使用指定的接入点

# 获取模拟面试 API 配置
INTERVIEW_API_KEY = os.getenv("INTERVIEW_API_KEY")
INTERVIEW_MODEL_ID = os.getenv("INTERVIEW_MODEL_ID")

if ARK_API_KEY:
    client = OpenAI(
        api_key=ARK_API_KEY,
        base_url="https://ark.cn-beijing.volces.com/api/v3",
    )
    print(f"[LLM] 初始化成功，使用火山方舟模型: {MODEL}", file=sys.stderr, flush=True)
else:
    client = None
    print("[LLM] 错误: 未检测到 ARK_API_KEY！", file=sys.stderr, flush=True)
    print("       请在 .env 文件中设置 ARK_API_KEY", file=sys.stderr, flush=True)

# 模拟面试API客户端初始化
if INTERVIEW_API_KEY and INTERVIEW_MODEL_ID:
    print(f"[Interview LLM] 初始化成功，使用模型ID: {INTERVIEW_MODEL_ID}", file=sys.stderr, flush=True)
else:
    print("[Interview LLM] 警告: 未检测到模拟面试 API 配置", file=sys.stderr, flush=True)


def search_web(question: str) -> str:
    """通过网络搜索获取面试问题"""
    try:
        print(f"[Web Search] 正在搜索: {question[:50]}...", file=sys.stderr, flush=True)
        
        # 使用百度搜索 API (免费)
        url = "https://www.baidu.com/s"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        params = {
            "wd": question,
            "rn": 5,
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            # 简单提取搜索结果摘要
            content = response.text
            # 提取百度搜索结果中的片段
            import re
            snippets = re.findall(r'<span class="c-color-gray">([^<]+)</span>', content)
            if not snippets:
                snippets = re.findall(r'"(-?\d+)"', content)[:5]
            
            if snippets:
                result = " | ".join([s.strip() for s in snippets[:3] if len(s.strip()) > 10])
                print(f"[Web Search] 搜索成功", file=sys.stderr, flush=True)
                return result
            return ""
        else:
            print(f"[Web Search] 搜索失败: {response.status_code}", file=sys.stderr, flush=True)
            return ""
            
    except Exception as e:
        print(f"[Web Search] 搜索异常: {str(e)}", file=sys.stderr, flush=True)
        return ""


def chat(system_prompt: str, user_message: str) -> str:
    """调用大模型获取回复"""
    if not client:
        raise Exception("未配置 ARK_API_KEY！请在 .env 文件中设置")

    try:
        print(f"[LLM] 正在调用 API...", file=sys.stderr, flush=True)
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
            max_tokens=4096,
        )
        print(f"[LLM] API 调用成功", file=sys.stderr, flush=True)
        return response.choices[0].message.content or 'AI暂无回复，请稍后重试'
    except Exception as e:
        error_msg = str(e)
        print(f"[LLM] API 调用失败: {error_msg}", file=sys.stderr, flush=True)
        if "api_key" in error_msg.lower() or "auth" in error_msg.lower() or "invalid" in error_msg.lower():
            raise Exception("API密钥无效，请检查 ARK_API_KEY 是否正确")
        elif "model" in error_msg.lower() or "not found" in error_msg.lower():
            raise Exception(f"模型 '{MODEL}' 不存在，请检查 ARK_MODEL 配置")
        elif "rate limit" in error_msg.lower() or "quota" in error_msg.lower():
            raise Exception("API调用额度已用尽或触发限流")
        else:
            raise Exception(f"AI服务调用失败: {error_msg}")


def get_mock_response(system_prompt: str, user_message: str) -> str:
    """当API不可用时返回提示"""
    return "[演示模式] 未检测到有效的 API 密钥，请配置 ARK_API_KEY"


def query_knowledge_base(question: str) -> str:
    """查询知识库获取答案"""
    if not INTERVIEW_API_KEY or not INTERVIEW_MODEL_ID:
        raise Exception("未配置知识库 API！请检查 INTERVIEW_API_KEY 和 INTERVIEW_MODEL_ID")

    try:
        print(f"[Knowledge Base] 正在查询知识库: {question[:50]}...", file=sys.stderr, flush=True)
        
        knowledge_base_domain = "api-knowledgebase.mlp.cn-beijing.volces.com"
        
        request_params = {
            "service_resource_id": INTERVIEW_MODEL_ID,
            "messages": [{"role": "user", "content": question}],
            "stream": False
        }
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json;charset=UTF-8",
            "Host": knowledge_base_domain,
            "Authorization": f"Bearer {INTERVIEW_API_KEY}"
        }
        
        url = f"http://{knowledge_base_domain}/api/knowledge/service/chat"
        
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(request_params),
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"[Knowledge Base] 返回结果: {json.dumps(result, ensure_ascii=False)[:500]}", file=sys.stderr, flush=True)
            
            if 'result_list' in result and len(result['result_list']) > 0:
                return result['result_list'][0].get('content', '')
            elif 'data' in result:
                return str(result['data'])
            elif 'content' in result:
                return result['content']
            else:
                return str(result)
        else:
            print(f"[Knowledge Base] API返回错误: {response.status_code} - {response.text}", file=sys.stderr, flush=True)
            return ""
            
    except Exception as e:
        print(f"[Knowledge Base] 查询失败: {str(e)}", file=sys.stderr, flush=True)
        return ""


def interview_chat(system_prompt: str, user_message: str, conversation_history: list = None, target_role: str = "") -> str:
    """调用大模型进行模拟面试对话，结合知识库获取面试题目"""
    if not client:
        raise Exception("未配置 ARK_API_KEY！请在 .env 文件中设置火山方舟API密钥")

    try:
        print(f"[Interview LLM] 正在调用大模型...", file=sys.stderr, flush=True)
        
        # 构建消息列表
        messages = []
        
        # 添加系统提示词
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 添加对话历史
        if conversation_history:
            messages.extend(conversation_history)
        
        # 添加当前用户消息
        if user_message:
            messages.append({"role": "user", "content": user_message})
        
        # 如果需要从知识库获取面试题目
        if "[查询知识库]" in user_message:
            # 从消息中提取要查询的内容
            query = user_message.replace("[查询知识库]", "").strip()
            knowledge_content = query_knowledge_base(query)
            
            # 更新最后一条用户消息，加入知识库内容
            if messages[-1]["role"] == "user":
                messages[-1]["content"] = f"""请基于以下知识库内容回答问题：

【知识库内容】
{knowledge_content if knowledge_content else '（知识库暂无相关内容，请基于一般知识回答）'}

【用户问题】
{query}"""
        
        # 调用通用大模型
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.8,
            max_tokens=2048,
        )
        
        print(f"[Interview LLM] API 调用成功", file=sys.stderr, flush=True)
        return response.choices[0].message.content or 'AI暂无回复，请稍后重试'
        
    except Exception as e:
        error_msg = str(e)
        print(f"[Interview LLM] API 调用失败: {error_msg}", file=sys.stderr, flush=True)
        if "api_key" in error_msg.lower() or "auth" in error_msg.lower() or "invalid" in error_msg.lower() or "401" in error_msg:
            raise Exception("API密钥无效，请检查 ARK_API_KEY 是否正确")
        elif "model" in error_msg.lower() or "not found" in error_msg.lower():
            raise Exception(f"模型 '{MODEL}' 不存在，请检查 ARK_MODEL 配置")
        elif "rate limit" in error_msg.lower() or "quota" in error_msg.lower():
            raise Exception("API调用额度已用尽或触发限流")
        else:
            raise Exception(f"模拟面试AI服务调用失败: {error_msg}")
