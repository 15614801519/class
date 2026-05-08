import fitz  # PyMuPDF
import os


def extract_text_from_pdf(file_path: str) -> str:
    """从PDF文件中提取文本内容"""
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text.strip()
    except Exception as e:
        raise Exception(f"PDF解析失败: {str(e)}")


def extract_text_from_file(file_path: str) -> str:
    """根据文件类型提取文本"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext in ('.txt', '.md'):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    else:
        raise Exception("不支持的文件格式，请上传PDF或文本文件")
