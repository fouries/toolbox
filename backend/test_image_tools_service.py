import base64
from io import BytesIO

from PIL import Image
from fastapi.testclient import TestClient

from api.image_tools import get_image_toolbox_service
from main import app


def make_image(fmt='PNG'):
    buf = BytesIO()
    Image.new('RGB', (120, 80), 'red').save(buf, format=fmt)
    return buf.getvalue()


def test_image_toolbox_compress_convert_resize_watermark_base64():
    service = get_image_toolbox_service()
    raw = make_image()
    b64 = base64.b64encode(raw).decode('ascii')

    compressed = service.process_base64('demo.png', b64, 'compress', {'quality': 60})
    assert compressed['code'] == 200
    assert compressed['filename'].endswith('.png')

    converted = service.process_base64('demo.png', b64, 'convert', {'target_format': 'jpg', 'quality': 70})
    assert converted['code'] == 200
    assert converted['media_type'] == 'image/jpeg'

    resized = service.process_base64('demo.png', b64, 'resize', {'width': 60})
    assert resized['code'] == 200
    im = Image.open(BytesIO(resized['content']))
    assert im.width == 60

    watermarked = service.process_base64('demo.png', b64, 'watermark', {'watermark': '测试'})
    assert watermarked['code'] == 200

    encoded = service.process_base64('demo.png', b64, 'base64', {})
    assert encoded['code'] == 200
    assert encoded['data']['text'].startswith('data:image/png;base64,')


def test_barcode_api_generates_png():
    client = TestClient(app)
    res = client.get('/api/barcode', params={'text': 'ABC123'})
    assert res.status_code == 200
    data = res.json()['data']
    assert data['base64'].startswith('data:image/png;base64,')
