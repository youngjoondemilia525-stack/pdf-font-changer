import streamlit as st
import fitz
import zipfile
import io


def replace_font_stream(input_bytes, target_font):
    """在内存中替换 PDF 字体，并返回字节流"""
    doc = fitz.open(stream=input_bytes, filetype="pdf")

    for page in doc:
        text_instances = []
        text_dict = page.get_text("dict")

        # 提取文字信息
        for block in text_dict.get("blocks", []):
            if block.get("type") == 0:  # 文本块
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if text:
                            text_instances.append({
                                "bbox": fitz.Rect(span["bbox"]),
                                "text": text,
                                "origin": fitz.Point(span["origin"]),
                                "size": span["size"]
                            })

        # 擦除并重绘
        for item in text_instances:
            rect = item["bbox"]
            # 扩大擦除范围，防止旧字体边缘残留
            rect.x0 -= 0.5
            rect.y0 -= 0.5
            rect.x1 += 0.5
            rect.y1 += 0.5

            # 画白色方块覆盖旧字
            page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))

            # 用新字体写上去
            page.insert_text(
                item["origin"],
                item["text"],
                fontname=target_font,
                fontsize=item["size"],
                color=(0, 0, 0)
            )

    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes


# ============ 网页 UI 设计 ============
st.set_page_config(page_title="PDF 防混淆字体替换器", page_icon="🔤")

st.title("🔤 PDF 防混淆字体批量替换器")
st.write("专门解决热敏打印机标签数字/字母易混淆（如 I/J, 0/O）的问题。支持一次拖入多个文件，批量转换。")

# 字体映射字典，使用 PDF 核心内置字体，确保云端无需配置即可运行
# 字体映射字典，使用 PDF 核心内置字体，确保云端无需配置即可运行
# 字体映射字典，使用 PDF 核心内置字体，确保云端无需配置即可运行
FONT_MAP = {
    "Courier (常规等宽，防混淆)": "cour",
    "Courier-Bold (加粗等宽，更醒目)": "cobo",
    "Helvetica (常规黑体，无衬线)": "helv",
    "Helvetica-Bold (加粗黑体)": "hebo",
    "Times-Roman (常规宋体，有衬线)": "tiro",
    "Times-Bold (加粗宋体)": "tibo"
}

# 字体选择器
selected_font_label = st.radio(
    "🎨 请选择要替换的目标字体：",
    list(FONT_MAP.keys())
)
target_font_code = FONT_MAP[selected_font_label]

st.info(
    "💡 提示：如果原来的文字离上方条码非常近，替换时白色覆盖框有极小概率会遮挡条码底部。建议首次使用时先扫码测试一下结果文件。")

# 批量上传组件
uploaded_files = st.file_uploader("📥 请选择要替换字体的 PDF 文件（可多选）", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    st.write(f"📁 已准备就绪 {len(uploaded_files)} 个文件。")
    
    if st.button("🚀 开始转换", type="primary"):
        with st.spinner('正在火速处理中，请稍候...'):
            try:
                # 判断：如果是单文件，直接输出 PDF
                if len(uploaded_files) == 1:
                    file = uploaded_files[0]
                    input_bytes = file.read()
                    
                    # 执行替换
                    output_bytes = replace_font_stream(input_bytes, target_font_code)
                    
                    st.success(f"✅ 成功替换文件：{file.name}")
                    
                    # 提供单文件 PDF 下载
                    st.download_button(
                        label=f"⬇️ 下载转换后的 PDF",
                        data=output_bytes,
                        file_name=f"新字体_{file.name}",
                        mime="application/pdf"
                    )
                
                # 判断：如果是多文件，走 ZIP 打包流程
                else:
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                        for file in uploaded_files:
                            input_bytes = file.read()
                            output_bytes = replace_font_stream(input_bytes, target_font_code)
                            new_filename = f"新字体_{file.name}"
                            zip_file.writestr(new_filename, output_bytes)
                    
                    st.success(f"✅ 成功替换并打包了 {len(uploaded_files)} 个文件！")
                    
                    # 提供 ZIP 下载
                    st.download_button(
                        label=f"📦 ⬇️ 一键下载全部结果 (ZIP)",
                        data=zip_buffer.getvalue(),
                        file_name="防混淆字体标签_批量打包.zip",
                        mime="application/zip"
                    )
                    
            except Exception as e:
                st.error(f"处理失败，错误信息: {str(e)}")
