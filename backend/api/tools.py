import io
import base64
import qrcode
from typing import Dict, Any

class ToolsService:
    """本地工具服务（无需调用第三方API）"""
    
    @staticmethod
    def generate_qrcode(text: str, size: int = 256) -> Dict[str, Any]:
        """生成二维码"""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=4,
            )
            qr.add_data(text)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # 调整大小
            if size != 256:
                img = img.resize((size, size))
            
            # 转换为base64
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return {
                "code": 200,
                "msg": "success",
                "data": {
                    "base64": f"data:image/png;base64,{img_str}",
                    "text": text
                }
            }
        except Exception as e:
            return {"code": 500, "msg": f"生成失败: {str(e)}"}
    


    @staticmethod
    def generate_barcode(text: str, height: int = 120) -> Dict[str, Any]:
        """生成 Code39 条形码（支持英文大写、数字和常见符号）。"""
        from PIL import Image, ImageDraw, ImageFont
        patterns = {
            '0':'nnnwwnwnn','1':'wnnwnnnnw','2':'nnwwnnnnw','3':'wnwwnnnnn','4':'nnnwwnnnw','5':'wnnwwnnnn','6':'nnwwwnnnn','7':'nnnwnnwnw','8':'wnnwnnwnn','9':'nnwwnnwnn',
            'A':'wnnnnwnnw','B':'nnwnnwnnw','C':'wnwnnwnnn','D':'nnnnwwnnw','E':'wnnnwwnnn','F':'nnwnwwnnn','G':'nnnnnwwnw','H':'wnnnnwwnn','I':'nnwnnwwnn','J':'nnnnwwwnn',
            'K':'wnnnnnnww','L':'nnwnnnnww','M':'wnwnnnnwn','N':'nnnnwnnww','O':'wnnnwnnwn','P':'nnwnwnnwn','Q':'nnnnnnwww','R':'wnnnnnwwn','S':'nnwnnnwwn','T':'nnnnwnwwn',
            'U':'wwnnnnnnw','V':'nwwnnnnnw','W':'wwwnnnnnn','X':'nwnnwnnnw','Y':'wwnnwnnnn','Z':'nwwnwnnnn','-':'nwnnnnwnw','.':'wwnnnnwnn',' ':'nwwnnnwnn','*':'nwnnwnwnn','$':'nwnwnwnnn','/':'nwnwnnnwn','+':'nwnnnwnwn','%':'nnnwnwnwn'
        }
        raw = str(text or '').upper().strip()[:64]
        if not raw:
            return {"code": 400, "msg": "请输入条形码内容"}
        if any(ch not in patterns or ch == '*' for ch in raw):
            return {"code": 400, "msg": "Code39 仅支持英文大写、数字、空格和 -.$/+%"}
        encoded = f"*{raw}*"
        narrow, wide, gap = 2, 5, 2
        bar_height = max(80, min(int(height or 120), 240))
        width = 40 + sum((wide if c == 'w' else narrow) for ch in encoded for c in patterns[ch]) + gap * (len(encoded) - 1)
        img = Image.new('RGB', (width, bar_height + 42), 'white')
        draw = ImageDraw.Draw(img)
        x = 20
        for idx, ch in enumerate(encoded):
            for pos, c in enumerate(patterns[ch]):
                w = wide if c == 'w' else narrow
                if pos % 2 == 0:
                    draw.rectangle((x, 10, x + w - 1, 10 + bar_height), fill='black')
                x += w
            if idx != len(encoded) - 1:
                x += gap
        try:
            font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), raw, font=font)
            draw.text(((width - (bbox[2]-bbox[0])) / 2, bar_height + 18), raw, fill='black', font=font)
        except Exception:
            pass
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return {"code": 200, "msg": "success", "data": {"base64": f"data:image/png;base64,{img_str}", "text": raw}}

    @staticmethod
    def generate_password(length: int = 16, 
                         include_upper: bool = True,
                         include_lower: bool = True,
                         include_number: bool = True,
                         include_symbol: bool = True) -> Dict[str, Any]:
        """生成随机密码"""
        import secrets
        import string
        
        chars = ""
        if include_upper:
            chars += string.ascii_uppercase
        if include_lower:
            chars += string.ascii_lowercase
        if include_number:
            chars += string.digits
        if include_symbol:
            chars += "!@#$%^&*()_+-="
        
        if not chars:
            return {"code": 400, "msg": "至少选择一种字符类型"}
        
        length = min(max(length, 4), 64)  # 限制长度
        password = ''.join(secrets.choice(chars) for _ in range(length))
        
        return {
            "code": 200,
            "msg": "success",
            "data": {
                "password": password,
                "length": length
            }
        }
    
    @staticmethod
    def base64_encode(text: str) -> Dict[str, Any]:
        """Base64编码"""
        try:
            encoded = base64.b64encode(text.encode('utf-8')).decode('utf-8')
            return {
                "code": 200,
                "msg": "success",
                "data": {"encoded": encoded}
            }
        except Exception as e:
            return {"code": 500, "msg": str(e)}
    
    @staticmethod
    def base64_decode(encoded: str) -> Dict[str, Any]:
        """Base64解码"""
        try:
            decoded = base64.b64decode(encoded).decode('utf-8')
            return {
                "code": 200,
                "msg": "success",
                "data": {"decoded": decoded}
            }
        except Exception as e:
            return {"code": 500, "msg": f"解码失败: {str(e)}"}
    
    @staticmethod
    def url_encode(text: str) -> Dict[str, Any]:
        """URL编码"""
        from urllib.parse import quote, unquote
        try:
            encoded = quote(text)
            return {
                "code": 200,
                "msg": "success",
                "data": {"encoded": encoded}
            }
        except Exception as e:
            return {"code": 500, "msg": str(e)}
    
    @staticmethod
    def url_decode(encoded: str) -> Dict[str, Any]:
        """URL解码"""
        from urllib.parse import quote, unquote
        try:
            decoded = unquote(encoded)
            return {
                "code": 200,
                "msg": "success",
                "data": {"decoded": decoded}
            }
        except Exception as e:
            return {"code": 500, "msg": str(e)}
    
    @staticmethod
    def json_format(json_str: str, indent: int = 2) -> Dict[str, Any]:
        """JSON格式化"""
        import json
        try:
            data = json.loads(json_str)
            formatted = json.dumps(data, indent=indent, ensure_ascii=False)
            return {
                "code": 200,
                "msg": "success",
                "data": {"formatted": formatted}
            }
        except json.JSONDecodeError as e:
            return {"code": 400, "msg": f"JSON格式错误: {str(e)}"}
