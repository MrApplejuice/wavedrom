import sys
import os
import shutil
import io

import base64
import json
import lzma
import jinja2
import falcon
import tempfile
import subprocess

from contextlib import closing
from PIL import Image, ImageDraw, ImageFont

from urllib.parse import urlencode

import pyparsing as pp
import browser_json

class ImageGenerationFailed(Exception):
    pass

def render_image_error(text):
    text = text.strip()
    with closing(Image.new("RGBA", (600, 300), (0, 0, 0, 0))) as image:
        max_width = 100
        max_height = 0
        
        draw = ImageDraw.Draw(image)
        try:
            font = ImageFont.truetype(font="Arial", size=20)
        except OSError:
            font = ImageFont.truetype(font="DejaVuSansMono", size=20)
        
        x_offset, _ = draw.textsize("Error: ", font=font)
        draw.text((0, 0), "Error: ", fill=(255, 0, 0, 255))
        
        w, h = draw.textsize(text, font=font)
        max_width = min(max(max_width, w + x_offset), image.width)
        max_height = min(max(max_height, h), image.height)
        
        draw.text((x_offset, 0), text, fill=(0, 0, 0, 255))
        
        with closing(image.crop((0, 0, max_width, max_height))) as subimage:
            with closing(io.BytesIO()) as io_out:
                subimage.save(io_out, "PNG")
                return io_out.getvalue()

def generate_image(image_type, scale, code):
    #print("------- code start ----------")
    #print(type(code))
    #print(code)
    
    #print("------- code normalized ----------")
    try:
        code = json.dumps(browser_json.parse_browser_json(code.decode() if isinstance(code, bytes) else code))
    except pp.ParseException as e:
        return render_image_error(str(e))
    #print(code)
    #print("------- code end ----------")
    
    try:
        tmpdir = tempfile.mkdtemp()

        filename = os.path.join(tmpdir, "out")
        process_result = subprocess.run(
            ["phantomjs", "server/serverside-renderer.js", "--silent", "--format={}".format(image_type), "--scale={}".format(scale), filename],
            cwd=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."),
            input=code if isinstance(code, bytes) else code.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
       
        #print(process_result.args)
        #print(process_result.returncode)
        #print(process_result.stdout)
        #print(process_result.stderr)

        if process_result.returncode == 0:
            with open(filename, "rb") as f:
                return f.read()
        else:
            return render_image_error(process_result.stdout.decode())
    finally:
        shutil.rmtree(tmpdir)
    return None

def derive_host_url(req):
    port_ext = ""
    if req.port != 80:
        port_ext = ":{}".format(req.port)
    return req.scheme + "://" + req.host + port_ext

class HTMLContent:
    def __init__(self):
        self.resource_path = os.path.join(
            os.path.dirname(__file__),
            "templates")
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.resource_path))

    def on_get(self, req, response, filename=None):
        if filename is None:
            filename = "index.html"

        extension = os.path.splitext(filename.lower())[1]
        inferred_mediatype = falcon.MEDIA_TEXT
        if extension == ".html":
            inferred_mediatype = falcon.MEDIA_HTML
        elif extension == ".css":
            inferred_mediatype = "text/css"
        elif extension == ".js":
            inferred_mediatype = falcon.MEDIA_JS
        elif extension == ".png":
            inferred_mediatype = falcon.MEDIA_PNG
        elif extension in (".jpg", ".jpeg"):
            inferred_mediatype = falcon.MEDIA_JPEG

        try:
            template = self.jinja_env.get_template(filename)
        except jinja2.exceptions.TemplateNotFound:
            raise falcon.HTTPNotFound(
                title="Page not found",
                description="The page '{}' does not exist".format(filename))
        else:
            port_ext = ""
            if req.port != 80:
                port_ext = ":{}".format(req.port)
            rendered_page = template.render(
                hostname=req.host + port_ext,
                protocol=req.scheme)
            response.body = rendered_page
            response.content_type = inferred_mediatype


def verify_image_type(image_type):
    if image_type not in ("svg", "png"):
        raise falcon.HTTPInternalServerError(
            title="Invalid type parameter",
            description="type parameter must be svg or png")

def parse_image_scale(scale):
    try:
        scale = float(scale)
        if not (.1 <= scale <= 10.0):
            raise ValueError()
    except ValueError:
        raise falcon.HTTPInternalServerError(
            title="Invalid scale parameter",
            description="Scale must be a valid float between .1 and 10.0")
    else:
        return scale

def compress_text(text):
    return base64.b64encode(
        lzma.compress(text.encode() if isinstance(text, str) 
                      else code)).decode()

def decompress_text(text):
    try:
        binary_lzma_code = base64.b64decode(text)
    except ValueError:
        raise falcon.HTTPInternalServerError(
            title="Code is not base64 encoded",
            description="The provided code is not encoded in the base64 format")

    try:
        plain_code = lzma.decompress(binary_lzma_code)
    except lzma.LZMAError:
        raise falcon.HTTPInternalServerError(
            title="Code is not compressed",
            description="The provided code is note compressed using the correct lzma compression technique")

    if isinstance(plain_code, str):
        plain_code = plain_code.encode()
        
    return plain_code

class RestAPI:
    def on_get(self, req, response, cmd="[None]"):
        cmd = cmd.lower()
        if cmd == "gen_image":
            image_type = req.get_param("type", required=True).lower()
            verify_image_type(image_type)

            scale = req.get_param("scale", default=1.0)
            scale = parse_image_scale(scale)

            code = req.get_param("c", required=True)
            
            plain_code = decompress_text(code.encode())

            image = generate_image(image_type, scale, plain_code)
            if image is None:
                raise falcon.HTTPInternalServerError(
                    title="Image generation failed",
                    description="The code you submitted could not be used to render a wavedrom image")

            response.content_type = {
                    "svg": "image/svg+xml",
                    "png": falcon.MEDIA_PNG
                }[image_type]
            response.body = image
        else:
            raise falcon.HTTPNotFound(
                title="invalid command",
                description="get command {} does not exist".format(cmd))

    def on_post(self, req, response, cmd="[None]"):
        cmd = cmd.lower()
        if cmd == "gen_image":
            return self.on_get(req, response, cmd=cmd)
        if cmd == "generate_link":
            scale = req.get_param("scale", default=1.0)
            scale = parse_image_scale(scale)

            image_type = req.get_param("type", default="png").lower()
            verify_image_type(image_type)

            auto_redirect = req.get_param_as_bool("redirect")

            code = req.get_param("code")
            if code is None:
                code = req.bounded_stream.read(32768)
            try:
                generate_image("svg", 1.0, code)
            except ImageGenerationFailed:
                raise falcon.HTTPInternalServerError(
                    title="Invalid WaveDrom code",
                    description="The WaveDrom code you submitted cannot be parsed by the WaveDrom generator")

            compressed_code = compress_text(code.decode() if isinstance(code, bytes) else code)

            url = "{hosturl}/rest/gen_image?{options}".format(
                hosturl=derive_host_url(req),
                options=urlencode({
                    "type": image_type,
                    "scale": scale,
                    "c": compressed_code}))

            if auto_redirect:
                raise falcon.HTTPTemporaryRedirect(url)

            response.content_type = falcon.MEDIA_TEXT
            response.body = url
        else:
            raise falcon.HTTPNotFound(
                title="invalid command",
                description="post command {} does not exist".format(cmd))

class StaticRedirect:
    def __init__(self, path):
        self.path = path

    def on_get(self, req, response):
        raise falcon.HTTPTemporaryRedirect(self.path)

    def on_post(self, req, response):
        raise falcon.HTTPTemporaryRedirect(self.path)

if __name__ in ("__main__", "main"):
    html_content = HTMLContent()
    rest_api = RestAPI()
    
    fapi = falcon.API()

    fapi.req_options.auto_parse_form_urlencoded = True

    fapi.add_route("/", StaticRedirect("html"))
    fapi.add_route("/html/", StaticRedirect("index.html"))

    fapi.add_route("/html/{filename}", html_content)

    fapi.add_route("/rest/", rest_api)
    fapi.add_route("/rest/{cmd}", rest_api)

