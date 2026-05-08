import os
import tempfile
from flask import Flask, render_template, request, jsonify, send_file
from utils.llm import chat, interview_chat, query_knowledge_base, search_web
from utils.pdf_parser import extract_text_from_file
from utils.pdf_generator import generate_resume_pdf

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB上传限制


# ==================== 页面路由 ====================

@app.route('/')
def index():
    features = [
        {'href': '/resume-optimize', 'icon': '✨', 'title': 'AI简历优化', 'desc': '基于大模型智能分析简历，提供专业的优化建议和改写方案，让您的简历脱颖而出', 'gradient': 'linear-gradient(135deg,#3b82f6,#06b6d4)', 'shadow': 'rgba(59,130,246,0.15)'},
        {'href': '/job-match', 'icon': '🎯', 'title': '岗位匹配', 'desc': '输入目标岗位描述，AI精准匹配简历与岗位的契合度，发现差距与提升方向', 'gradient': 'linear-gradient(135deg,#7c3aed,#8b5cf6)', 'shadow': 'rgba(124,58,237,0.15)'},
        {'href': '/career-assess', 'icon': '🧭', 'title': '职业测评', 'desc': '通过科学的职业测评问卷，结合AI分析，帮助您找到最适合的职业方向', 'gradient': 'linear-gradient(135deg,#059669,#14b8a6)', 'shadow': 'rgba(16,185,129,0.15)'},
        {'href': '/resume-generate', 'icon': '📝', 'title': '简历生成', 'desc': '填写信息后自动生成专业简历，支持多种模板，一键导出PDF格式', 'gradient': 'linear-gradient(135deg,#f97316,#f59e0b)', 'shadow': 'rgba(249,115,22,0.15)'},
        {'href': '/resume-evaluate', 'icon': '📊', 'title': '简历评价', 'desc': 'AI多维度评估简历质量，从内容完整性、专业性、排版等维度给出评分和改进建议', 'gradient': 'linear-gradient(135deg,#e11d48,#ec4899)', 'shadow': 'rgba(225,29,72,0.15)'},
        {'href': '/interview', 'icon': '💼', 'title': '模拟面试', 'desc': 'AI智能模拟真实面试场景，实时互动问答，助您提升面试技巧和自信心', 'gradient': 'linear-gradient(135deg,#4f46e5,#3b82f6)', 'shadow': 'rgba(79,70,229,0.15)'},
    ]
    return render_template('index.html', features=features)

@app.route('/resume-optimize')
def resume_optimize():
    return render_template('resume_optimize.html')

@app.route('/job-match')
def job_match():
    return render_template('job_match.html')

@app.route('/career-assess')
def career_assess():
    return render_template('career_assess.html')

@app.route('/resume-generate')
def resume_generate():
    return render_template('resume_generate.html')

@app.route('/resume-evaluate')
def resume_evaluate():
    return render_template('resume_evaluate.html')

@app.route('/interview')
def interview():
    return render_template('interview.html')


@app.route('/api/interview-chat', methods=['POST'])
def api_interview_chat():
    """模拟面试对话接口"""
    print(f"\n[API] 收到 /api/interview-chat 请求", flush=True)
    
    data = request.json
    system_prompt = data.get('system_prompt', '')
    user_message = data.get('user_message', '')
    conversation_history = data.get('conversation_history', [])
    target_role = data.get('target_role', '')
    
    print(f"[API] system_prompt长度: {len(system_prompt)}, user_message长度: {len(user_message)}, 历史消息数: {len(conversation_history)}", flush=True)
    
    if not system_prompt:
        print("[API] 参数缺失", flush=True)
        return jsonify({'error': '请提供system_prompt参数'}), 400
    
    try:
        # 判断职业是否与计算机网络相关
        network_keywords = ['网络', '运维', '安全', '渗透', '安全工程师', '网络工程师', 
                           '运维工程师', '系统管理员', 'DevOps', 'SRE', '云计算', 
                           '网络管理员', '售前', '售后', '售中', '网络运维', 'IT运维']
        is_network_related = any(keyword in target_role for keyword in network_keywords)
        
        if user_message and target_role:
            if is_network_related:
                # 计算机网络相关，只用知识库
                print(f"[API] 正在查询知识库获取下一个面试问题...", flush=True)
                kb_query = f"{target_role}岗位，基于候选人刚回答的「{user_message[:100]}」，从题库中选出下一个最合适的问题（只输出问题，不要解释）"
                kb_content = query_knowledge_base(kb_query)
                print(f"[API] 知识库返回: {kb_content[:300] if kb_content else '无内容'}...", flush=True)
                
                if kb_content:
                    enhanced_system_prompt = f"""{system_prompt}

【重要】用户刚回答了：「{user_message}」

根据知识库，请继续面试：
1. 先简短评价用户的回答（1-2句话）
2. 然后提出知识库中的下一个问题：{kb_content}

记住：必须问知识库中的问题，不要自己编造！"""
                    system_prompt = enhanced_system_prompt
                else:
                    return jsonify({'error': f'知识库中已无更多问题，面试结束。请结束面试并给予评价。'}), 400
            else:
                # 其他职业，可以编造问题
                print(f"[API] 正在基于专业知识编造下一个面试问题...", flush=True)
                enhanced_system_prompt = f"""{system_prompt}

【重要】用户刚回答了：「{user_message}」

请继续{target_role}岗位的面试：
1. 先简短评价用户的回答（1-2句话）
2. 然后基于该岗位专业知识，提出下一个合适的面试问题

注意：可以编造问题，但必须是{target_role}岗位真实可能问到的问题，不能胡编乱造！"""
                system_prompt = enhanced_system_prompt
        
        print(f"[API] 正在调用 interview_chat() 函数...", flush=True)
        result = interview_chat(system_prompt, user_message, conversation_history, target_role)
        print(f"[API] interview_chat() 返回成功，结果长度: {len(result)}", flush=True)
        return jsonify({'result': result})
    except Exception as e:
        print(f"[API] 发生错误: {str(e)}", flush=True)
        return jsonify({'error': f'模拟面试服务异常: {str(e)}'}), 500


@app.route('/api/interview-start', methods=['POST'])
def api_interview_start():
    """开始模拟面试，先从知识库获取面试题目"""
    print(f"\n[API] 收到 /api/interview-start 请求", flush=True)
    
    data = request.json
    target_role = data.get('target_role', '')
    
    if not target_role:
        return jsonify({'error': '请提供目标岗位'}), 400
    
    # 判断职业是否与计算机网络相关
    network_keywords = ['网络', '运维', '安全', '渗透', '安全工程师', '网络工程师', 
                       '运维工程师', '系统管理员', 'DevOps', 'SRE', '云计算', 
                       '网络管理员', '售前', '售后', '售中', '网络运维', 'IT运维']
    is_network_related = any(keyword in target_role for keyword in network_keywords)
    
    try:
        knowledge_content = ""
        
        if is_network_related:
            # 计算机网络相关职业，优先使用知识库
            print(f"[API] 检测到{target_role}与计算机网络相关，查询知识库...", flush=True)
            knowledge_query = f"请给出{target_role}岗位的常见面试问题，按顺序列出编号"
            knowledge_content = query_knowledge_base(knowledge_query)
            print(f"[API] 知识库返回内容: {knowledge_content[:500] if knowledge_content else '无内容'}...", flush=True)
            
            if not knowledge_content:
                return jsonify({'error': f'暂未找到{target_role}岗位的面试题库，请换个岗位名称试试'}), 400
            
            # 构建面试官系统提示词 - 严格按知识库提问
            system_prompt = f"""你是一位专业的{target_role}岗位面试官，正在对候选人进行模拟面试。

【严格规则】
1. 你必须严格按以下知识库的题目提问，禁止自己编造问题
2. 每次只问一个面试问题
3. 候选人回答后，从列表中选下一个问题继续问
4. 如果候选人回答不完整，补充对应的参考答案要点

知识库题目列表（必须按顺序使用）：
---
{knowledge_content}
---

面试流程：
1. 先请候选人做自我介绍
2. 询问列表中的第1个问题
3. 根据回答继续问后续问题
4. 面试结束时给予总体评价

注意：你只能问上面列表中的问题，绝对不能问列表以外的问题！"""
        else:
            # 其他职业，可以编造问题
            print(f"[API] {target_role}与计算机网络无关，使用通用面试题库...", flush=True)
            knowledge_query = f"{target_role}岗位面试常见问题和考察点"
            knowledge_content = search_web(knowledge_query)
            print(f"[API] 搜索返回: {knowledge_content[:500] if knowledge_content else '无内容'}...", flush=True)
            
            # 构建面试官系统提示词 - 可以编造但要正确
            system_prompt = f"""你是一位专业的{target_role}岗位面试官，正在对候选人进行模拟面试。

【面试要求】
1. 根据{target_role}岗位要求，每次问一个相关面试问题
2. 问题必须与岗位职能相关，可以基于以下参考题库，也可自行编造相关问题
3. 编造的问题必须是{target_role}岗位真实可能问到的问题，不能胡编乱造
4. 候选人回答后继续追问或问下一个问题
5. 面试结束时给予总体评价

参考题库：
---
{knowledge_content if knowledge_content else '（无参考，请基于专业知识编造正确的面试问题）'}
---

面试流程：
1. 先请候选人做自我介绍
2. 问第1个面试问题
3. 根据回答继续问后续问题
4. 面试结束时给予总体评价

注意：编造的问题必须专业、真实、符合该岗位特点！"""
        
        first_question = interview_chat(system_prompt, f"请开始{target_role}岗位的面试，我是候选人。", target_role=target_role)
        
        return jsonify({
            'success': True,
            'system_prompt': system_prompt,
            'first_question': first_question
        })
    except Exception as e:
        print(f"[API] 开始面试失败: {str(e)}", flush=True)
        return jsonify({'error': f'启动面试失败: {str(e)}'}), 500


# ==================== API路由 ====================

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """通用大模型对话接口"""
    print(f"\n[API] 收到 /api/chat 请求", flush=True)
    
    data = request.json
    system_prompt = data.get('system_prompt', '')
    user_message = data.get('user_message', '')
    
    print(f"[API] system_prompt长度: {len(system_prompt)}, user_message长度: {len(user_message)}", flush=True)
    
    if not system_prompt or not user_message:
        print("[API] 参数缺失", flush=True)
        return jsonify({'error': '请提供system_prompt和user_message参数'}), 400
    
    try:
        print(f"[API] 正在调用 chat() 函数...", flush=True)
        result = chat(system_prompt, user_message)
        print(f"[API] chat() 返回成功，结果长度: {len(result)}", flush=True)
        return jsonify({'result': result})
    except Exception as e:
        print(f"[API] 发生错误: {str(e)}", flush=True)
        return jsonify({'error': f'AI服务异常: {str(e)}'}), 500


@app.route('/api/upload-resume', methods=['POST'])
def api_upload_resume():
    """上传简历文件，提取文本"""
    if 'file' not in request.files:
        return jsonify({'error': '未找到上传文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    
    # 保存到临时文件
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        file.save(tmp)
        tmp_path = tmp.name
    
    try:
        text = extract_text_from_file(tmp_path)
        return jsonify({'text': text, 'filename': file.filename})
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        os.unlink(tmp_path)


@app.route('/api/generate-resume-pdf', methods=['POST'])
def api_generate_resume_pdf():
    """生成简历PDF并返回下载"""
    data = request.json
    
    # 处理技能列表
    skills_raw = data.get('skills', '')
    if isinstance(skills_raw, str):
        import re
        skills = [s.strip() for s in re.split(r'[,，、]', skills_raw) if s.strip()]
    else:
        skills = skills_raw
    
    resume_data = {
        'name': data.get('name', ''),
        'phone': data.get('phone', ''),
        'email': data.get('email', ''),
        'summary': data.get('summary', ''),
        'education': data.get('education', []),
        'experience': data.get('experience', []),
        'projects': data.get('projects', []),
        'skills': skills,
    }
    
    # 生成PDF到临时文件
    tmp_dir = tempfile.mkdtemp()
    filename = f"{resume_data['name'] or 'resume'}_简历.pdf"
    output_path = os.path.join(tmp_dir, filename)
    
    try:
        generate_resume_pdf(resume_data, output_path)
        return send_file(
            output_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf',
        )
    except Exception as e:
        return jsonify({'error': f'PDF生成失败: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
