"""
Run this once to install the correct app.py:
    python install_app.py
"""
content = r'''"""
File Canonicalizer v0.5 - Web Interface (no API key required)
Run:  python app.py
Open: http://localhost:5000
"""
from __future__ import annotations
import io
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify
from canonicalizer import canonicalize

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

def extract_text(file_bytes: bytes, filename: str):
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(file_bytes))
            text = "\n".join(p.extract_text() or "" for p in reader.pages)
            if not text.strip():
                return "", "PDF has no extractable text layer. Manual OCR required."
            return text, None
        except Exception as e:
            return "", f"PDF extraction failed: {e}"
    if ext == ".docx":
        try:
            from docx import Document
            doc = Document(io.BytesIO(file_bytes))
            return "\n".join(p.text for p in doc.paragraphs), None
        except Exception as e:
            return "", f"DOCX extraction failed: {e}"
    if ext in (".txt", ".md", ".csv", ".log", ""):
        return file_bytes.decode("utf-8", errors="replace"), None
    return "", f"Unsupported file type '{ext}'. Accepted: .pdf .docx .txt"

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/canonicalize", methods=["POST"])
def run():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "Empty filename."}), 400
    text, err = extract_text(f.read(), f.filename)
    if err:
        return jsonify({"result": {"check_result": "FAIL", "failure_reason": err}})
    result = canonicalize(text, f.filename)
    return jsonify({"result": result, "extracted_preview": text[:1000]})

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>File Canonicalizer v0.5</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:'Courier New',monospace;background:#0d1117;color:#e6edf3;min-height:100vh;padding:40px 24px}
    header{max-width:980px;margin:0 auto 36px;border-bottom:1px solid #21262d;padding-bottom:20px}
    header h1{font-size:1.3rem;color:#58a6ff;letter-spacing:.08em;text-transform:uppercase}
    header p{margin-top:6px;font-size:.8rem;color:#8b949e}
    .layout{max-width:980px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:20px}
    .panel{background:#161b22;border:1px solid #21262d;border-radius:6px;padding:22px}
    .panel h2{font-size:.72rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#8b949e;margin-bottom:18px}
    .drop{border:2px dashed #30363d;border-radius:6px;padding:40px 20px;text-align:center;cursor:pointer;transition:border-color .15s,background .15s;background:#0d1117}
    .drop.over{border-color:#58a6ff;background:#112035}
    .drop strong{color:#58a6ff;font-size:1rem}
    .drop p{font-size:.8rem;color:#8b949e;margin-top:8px}
    #fname{margin-top:12px;font-size:.78rem;color:#3fb950;min-height:18px}
    #preview-wrap{margin-top:14px;display:none}
    #preview-wrap label{font-size:.7rem;color:#8b949e;display:block;margin-bottom:4px}
    #preview{width:100%;height:90px;background:#0d1117;border:1px solid #21262d;border-radius:4px;color:#8b949e;font-family:'Courier New',monospace;font-size:.7rem;padding:8px;resize:none;overflow:auto}
    button{margin-top:16px;width:100%;padding:10px;background:#238636;border:1px solid #2ea043;border-radius:4px;color:#fff;font-family:'Courier New',monospace;font-size:.82rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;cursor:pointer;transition:background .15s}
    button:hover{background:#2ea043}
    button:disabled{background:#21262d;border-color:#30363d;color:#484f58;cursor:default}
    .badge{display:inline-block;font-size:.68rem;font-weight:700;letter-spacing:.12em;padding:3px 10px;border-radius:20px;margin-bottom:14px;text-transform:uppercase}
    .pass{background:#1a4731;color:#3fb950;border:1px solid #2ea043}
    .warn{background:#3d2a00;color:#d29922;border:1px solid #9e6a03}
    .fail{background:#3d1a1a;color:#f85149;border:1px solid #da3633}
    .idle{background:#21262d;color:#8b949e;border:1px solid #30363d}
    .result-box{background:#0d1117;border:1px solid #21262d;border-radius:4px;padding:14px;font-size:.75rem;line-height:1.6;white-space:pre-wrap;word-break:break-word;min-height:320px;color:#8b949e}
    .spinner{display:none;margin:60px auto;width:28px;height:28px;border:3px solid #30363d;border-top-color:#58a6ff;border-radius:50%;animation:spin .7s linear infinite}
    @keyframes spin{to{transform:rotate(360deg)}}
    .k{color:#79c0ff}.s{color:#a5d6ff}.nv{color:#ff7b72}
    #file-input{display:none}
    @media(max-width:640px){.layout{grid-template-columns:1fr}}
  </style>
</head>
<body>
<header>
  <h1>File Canonicalizer v0.5</h1>
  <p>Upload a PDF, DOCX, or TXT — get a canonical record and manifest · PASS / WARN / FAIL</p>
</header>
<div class="layout">
  <div class="panel">
    <h2>Upload Document</h2>
    <div class="drop" id="drop" onclick="document.getElementById('file-input').click()">
      <strong>Drop file here</strong>
      <p>or click to browse</p>
      <p style="margin-top:10px;font-size:.72rem">PDF · DOCX · TXT</p>
    </div>
    <input type="file" id="file-input" accept=".pdf,.docx,.txt,.md">
    <div id="fname">No file selected</div>
    <div id="preview-wrap">
      <label>Extracted text preview</label>
      <textarea id="preview" readonly></textarea>
    </div>
    <button id="btn" onclick="run()" disabled>&#9654; Canonicalize</button>
  </div>
  <div class="panel">
    <h2>Result</h2>
    <span class="badge idle" id="badge">READY</span>
    <div class="spinner" id="spinner"></div>
    <div class="result-box" id="output">Output will appear here after you upload and canonicalize a file.</div>
  </div>
</div>
<script>
let file=null;
const drop=document.getElementById('drop');
document.getElementById('file-input').addEventListener('change',e=>{if(e.target.files[0])setFile(e.target.files[0])});
drop.addEventListener('dragover',e=>{e.preventDefault();drop.classList.add('over')});
drop.addEventListener('dragleave',()=>drop.classList.remove('over'));
drop.addEventListener('drop',e=>{e.preventDefault();drop.classList.remove('over');if(e.dataTransfer.files[0])setFile(e.dataTransfer.files[0])});
function setFile(f){file=f;document.getElementById('fname').textContent=f.name+' ('+(f.size/1024).toFixed(1)+' KB)';document.getElementById('btn').disabled=false;}
async function run(){
  if(!file)return;
  const badge=document.getElementById('badge'),output=document.getElementById('output'),spinner=document.getElementById('spinner');
  badge.className='badge idle';badge.textContent='PROCESSING...';
  output.textContent='';spinner.style.display='block';
  document.getElementById('btn').disabled=true;
  const fd=new FormData();fd.append('file',file);
  try{
    const res=await fetch('/canonicalize',{method:'POST',body:fd});
    const data=await res.json();
    spinner.style.display='none';document.getElementById('btn').disabled=false;
    if(data.error){badge.className='badge fail';badge.textContent='ERROR';output.textContent=data.error;return;}
    if(data.extracted_preview){document.getElementById('preview').value=data.extracted_preview;document.getElementById('preview-wrap').style.display='block';}
    const r=data.result,cr=(r.check_result||'FAIL').toLowerCase();
    badge.className='badge '+cr;badge.textContent=cr.toUpperCase();
    output.innerHTML=hl(JSON.stringify(r,null,2));
  }catch(e){
    spinner.style.display='none';document.getElementById('btn').disabled=false;
    badge.className='badge fail';badge.textContent='ERROR';output.textContent='Request failed: '+e;
  }
}
function hl(j){return j.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"([^"]+)":/g,'<span class="k">"$1"</span>:').replace(/: "([^"]*)"/g,': <span class="s">"$1"</span>').replace(/: (null)/g,': <span class="nv">$1</span>');}
</script>
</body>
</html>"""

if __name__ == "__main__":
    print("Canonicalizer UI → http://localhost:5000")
    app.run(debug=True)
'''

with open("app.py", "w", encoding="utf-8") as fh:
    fh.write(content)

print("app.py written successfully.")
print("Now run:  python app.py")
