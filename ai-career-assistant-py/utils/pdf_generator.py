from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os


def _register_chinese_font():
    """尝试注册中文字体"""
    font_paths = [
        'C:/Windows/Fonts/msyh.ttc',    # 微软雅黑
        'C:/Windows/Fonts/simsun.ttc',   # 宋体
        'C:/Windows/Fonts/simhei.ttf',   # 黑体
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                pdfmetrics.registerFont(TTFont('ChineseFont', fp, subfontIndex=0))
                return 'ChineseFont'
            except Exception:
                continue
    return 'Helvetica'


def generate_resume_pdf(data: dict, output_path: str):
    """根据简历数据生成PDF文件"""
    font_name = _register_chinese_font()
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=20 * mm,
        bottomMargin=15 * mm,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
    )
    
    styles = getSampleStyleSheet()
    
    # 自定义样式
    name_style = ParagraphStyle(
        'NameStyle', parent=styles['Normal'],
        fontName=font_name, fontSize=22, leading=28,
        alignment=TA_CENTER, textColor=HexColor('#1e40af'),
        spaceAfter=4 * mm,
    )
    contact_style = ParagraphStyle(
        'ContactStyle', parent=styles['Normal'],
        fontName=font_name, fontSize=10, leading=14,
        alignment=TA_CENTER, textColor=HexColor('#6b7280'),
        spaceAfter=8 * mm,
    )
    section_title_style = ParagraphStyle(
        'SectionTitle', parent=styles['Normal'],
        fontName=font_name, fontSize=14, leading=18,
        textColor=HexColor('#1e40af'),
        spaceBefore=6 * mm, spaceAfter=3 * mm,
    )
    content_style = ParagraphStyle(
        'ContentStyle', parent=styles['Normal'],
        fontName=font_name, fontSize=10, leading=16,
        textColor=HexColor('#374151'),
        spaceAfter=2 * mm,
    )
    sub_title_style = ParagraphStyle(
        'SubTitle', parent=styles['Normal'],
        fontName=font_name, fontSize=11, leading=16,
        textColor=HexColor('#1f2937'),
        spaceAfter=1 * mm,
    )
    
    story = []
    
    # 姓名
    story.append(Paragraph(data.get('name', ''), name_style))
    
    # 联系方式
    contact_parts = []
    if data.get('phone'):
        contact_parts.append(data['phone'])
    if data.get('email'):
        contact_parts.append(data['email'])
    if contact_parts:
        story.append(Paragraph(' | '.join(contact_parts), contact_style))
    
    # 分隔线
    story.append(HRFlowable(width="100%", thickness=1.5, color=HexColor('#3b82f6'), spaceAfter=3 * mm))
    
    # 个人简介
    if data.get('summary'):
        story.append(Paragraph('个人简介', section_title_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#93c5fd'), spaceAfter=2 * mm))
        story.append(Paragraph(data['summary'], content_style))
    
    # 教育背景
    education = data.get('education', [])
    if education:
        story.append(Paragraph('教育背景', section_title_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#93c5fd'), spaceAfter=2 * mm))
        for edu in education:
            if edu.get('school'):
                title = f"{edu['school']} — {edu.get('major', '')} ({edu.get('degree', '')})"
                period = edu.get('period', '')
                if period:
                    title += f"  [{period}]"
                story.append(Paragraph(title, sub_title_style))
                if edu.get('description'):
                    story.append(Paragraph(edu['description'], content_style))
    
    # 工作经历
    experience = data.get('experience', [])
    if experience:
        story.append(Paragraph('工作经历', section_title_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#93c5fd'), spaceAfter=2 * mm))
        for exp in experience:
            if exp.get('company'):
                title = f"{exp['company']} — {exp.get('position', '')}"
                period = exp.get('period', '')
                if period:
                    title += f"  [{period}]"
                story.append(Paragraph(title, sub_title_style))
                if exp.get('description'):
                    story.append(Paragraph(exp['description'].replace('\n', '<br/>'), content_style))
    
    # 项目经历
    projects = data.get('projects', [])
    if projects:
        story.append(Paragraph('项目经历', section_title_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#93c5fd'), spaceAfter=2 * mm))
        for proj in projects:
            if proj.get('name'):
                title = f"{proj['name']} — {proj.get('role', '')}"
                period = proj.get('period', '')
                if period:
                    title += f"  [{period}]"
                story.append(Paragraph(title, sub_title_style))
                if proj.get('description'):
                    story.append(Paragraph(proj['description'].replace('\n', '<br/>'), content_style))
    
    # 技能特长
    skills = data.get('skills', [])
    if skills:
        story.append(Paragraph('技能特长', section_title_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#93c5fd'), spaceAfter=2 * mm))
        story.append(Paragraph(' | '.join(skills), content_style))
    
    doc.build(story)
    return output_path
