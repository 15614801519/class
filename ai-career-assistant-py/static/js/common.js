// ==================== 通用API调用 ====================
async function callAI(systemPrompt, userMessage) {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ system_prompt: systemPrompt, user_message: userMessage }),
  });
  const data = await res.json();
  if (data.error) throw new Error(data.error);
  return data.result;
}

// ==================== 文件上传 ====================
async function uploadResume(file) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch('/api/upload-resume', { method: 'POST', body: formData });
  const data = await res.json();
  if (data.error) throw new Error(data.error);
  return data;
}

// ==================== 简易Markdown渲染 ====================
function renderMarkdown(text) {
  if (!text) return '';
  let html = text
    // 表格
    .replace(/\n\|(.+)\|\n\|[-| :]+\|\n((?:\|.+\|\n?)*)/g, (match, header, body) => {
      const ths = header.split('|').map(s => s.trim()).filter(Boolean).map(s => `<th>${s}</th>`).join('');
      const rows = body.trim().split('\n').map(row => {
        const tds = row.split('|').map(s => s.trim()).filter(Boolean).map(s => `<td>${s}</td>`).join('');
        return `<tr>${tds}</tr>`;
      }).join('');
      return `<table><thead><tr>${ths}</tr></thead><tbody>${rows}</tbody></table>`;
    })
    // 标题
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    // 分隔线
    .replace(/^---$/gm, '<hr>')
    // 粗体和斜体
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // 行内代码
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    // 无序列表
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    // 有序列表
    .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
    // 段落（双换行）
    .replace(/\n\n/g, '</p><p>')
    // 单换行
    .replace(/\n/g, '<br>');
  
  // 包裹列表项
  html = html.replace(/((?:<li>.*<\/li><br>?)+)/g, (match) => {
    return '<ul>' + match.replace(/<br>/g, '') + '</ul>';
  });
  
  return `<p>${html}</p>`;
}

// ==================== 加载动画 ====================
function loadingHTML(text = 'AI分析中...') {
  return `<div style="display:flex;align-items:center;gap:0.75rem;justify-content:center;padding:2rem;color:#6b7280;">
    <div class="spinner" style="border-color:rgba(59,130,246,0.2);border-top-color:#3b82f6;"></div>
    <span>${text}</span>
  </div>`;
}

// ==================== 导航栏高亮 ====================
document.addEventListener('DOMContentLoaded', () => {
  const path = window.location.pathname;
  document.querySelectorAll('.nav-links a, .mobile-menu a').forEach(a => {
    if (a.getAttribute('href') === path) {
      a.classList.add('active');
    }
  });
  
  // 移动端菜单切换
  const toggle = document.getElementById('navToggle');
  const menu = document.getElementById('mobileMenu');
  if (toggle && menu) {
    toggle.addEventListener('click', () => {
      menu.classList.toggle('open');
    });
  }
});
