"""
PDF 解析服务
"""
import fitz  # PyMuPDF
import os
import tempfile
from PIL import Image
import io
import warnings
warnings.filterwarnings('ignore', category=Image.DecompressionBombWarning)


class PDFService:
    """PDF 文件解析服务"""

    def extract_text(self, file_path: str) -> str:
        """从 PDF 提取文本内容"""
        text = ""
        try:
            doc = fitz.open(file_path)
            for page in doc:
                text += page.get_text()
            doc.close()
        except Exception as e:
            print(f"PDF 解析错误: {e}")
        return text

    def get_page_count(self, file_path: str) -> int:
        """获取 PDF 页数"""
        try:
            doc = fitz.open(file_path)
            count = doc.page_count
            doc.close()
            return count
        except:
            return 0

    def extract_images(self, file_path: str, output_dir: str) -> list:
        """提取 PDF 中的图片"""
        images = []
        try:
            doc = fitz.open(file_path)
            for page_num, page in enumerate(doc):
                image_list = page.get_images()
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]

                    image_path = f"{output_dir}/page{page_num}_img{img_index}.{image_ext}"
                    with open(image_path, "wb") as f:
                        f.write(image_bytes)
                    images.append(image_path)
            doc.close()
        except Exception as e:
            print(f"图片提取错误: {e}")
        return images

    def pdf_to_images(self, file_path: str, output_dir: str = None, dpi: int = 200) -> list:
        """将PDF页面转换为图片（用于OCR）

        Args:
            file_path: PDF文件路径
            output_dir: 输出目录，None则使用临时目录
            dpi: 图片分辨率

        Returns:
            图片路径列表
        """
        if output_dir is None:
            output_dir = tempfile.gettempdir()

        images = []
        try:
            doc = fitz.open(file_path)
            for page_num in range(doc.page_count):
                page = doc[page_num]
                # 设置缩放比例
                zoom = dpi / 72
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)

                # 转换为PIL Image
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))

                # 保存图片
                img_path = os.path.join(output_dir, f"page_{page_num}.png")
                img.save(img_path)
                images.append(img_path)

            doc.close()
        except Exception as e:
            print(f"PDF转图片错误: {e}")

        return images

    def ocr_image(self, image_path: str) -> str:
        """OCR识别图片中的文字

        使用RapidOCR（轻量级，已安装）
        """
        text = ""

        # 使用RapidOCR（推荐，轻量级）
        try:
            from rapidocr_onnxruntime import RapidOCR
            ocr = RapidOCR()
            result, elapse = ocr(image_path)  # 直接调用
            if result:
                for line in result:
                    if line and len(line) >= 2:
                        # RapidOCR返回格式: [坐标, 文本, 置信度]
                        text += line[1] + "\n"
            if text.strip():
                return text
        except Exception as e:
            print(f"RapidOCR失败: {e}")

        # 方法2: 尝试EasyOCR
        try:
            import easyocr
            reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
            result = reader.readtext(image_path)
            for detection in result:
                text += detection[1] + "\n"
            if text.strip():
                return text
        except Exception as e:
            print(f"EasyOCR失败: {e}")

        # 方法3: 尝试Tesseract
        try:
            import pytesseract
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img, lang='chi_sim+eng')
            if text.strip():
                return text
        except Exception as e:
            print(f"Tesseract失败: {e}")

        return text

    def extract_text_with_ocr(self, file_path: str) -> str:
        """提取PDF文本，如果直接提取为空则使用OCR

        Args:
            file_path: PDF文件路径

        Returns:
            提取的文本内容
        """
        # 先尝试直接提取文本
        text = self.extract_text(file_path)
        if text.strip():
            return text

        # 如果直接提取为空，使用OCR
        print(f"PDF文本为空，使用OCR识别: {file_path}")
        images = self.pdf_to_images(file_path)

        all_text = []
        for img_path in images:
            ocr_text = self.ocr_image(img_path)
            all_text.append(ocr_text)
            # 清理临时图片
            try:
                os.remove(img_path)
            except:
                pass

        return "\n".join(all_text)
