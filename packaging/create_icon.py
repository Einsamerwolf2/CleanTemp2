"""Generate the project's vector-style icon at Windows icon resolutions."""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
assets = ROOT / 'assets'
assets.mkdir(exist_ok=True)
image = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0))
draw = ImageDraw.Draw(image)
draw.rounded_rectangle((24, 24, 1000, 1000), radius=216, fill='#0b1220', outline='#4dd4c7', width=32)
# Large, high-contrast broom with a clean silhouette.
draw.line((704, 236, 458, 560), fill='#f1f7ff', width=84)
draw.ellipse((662, 194, 746, 278), fill='#f1f7ff')
draw.polygon([(382, 476), (578, 624), (488, 842), (180, 610)], fill='#4dd4c7')
draw.line((388, 552, 252, 654), fill='#0b1220', width=25)
draw.line((440, 592, 324, 710), fill='#0b1220', width=25)
draw.line((494, 632, 398, 766), fill='#0b1220', width=25)
for x,y,s in ((756, 520, 82), (706, 756, 46)):
    draw.polygon([(x,y-s),(x+s//3,y-s//3),(x+s,y),(x+s//3,y+s//3),(x,y+s),(x-s//3,y+s//3),(x-s,y),(x-s//3,y-s//3)], fill='#f1f7ff')
image = image.resize((256,256), Image.Resampling.LANCZOS)
image.save(assets / 'cleantemp.png')
image.save(assets / 'cleantemp.ico', sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
# Keep the source artwork editable without a graphics editor.
(assets / 'cleantemp.svg').write_text('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024"><rect x="24" y="24" width="976" height="976" rx="216" fill="#0b1220" stroke="#4dd4c7" stroke-width="32"/><path d="M704 236 458 560" stroke="#f1f7ff" stroke-width="84" stroke-linecap="round"/><path d="m382 476 196 148-90 218-308-232Z" fill="#4dd4c7"/><path d="m388 552-136 102m188-62L324 710m170-78-96 134" stroke="#0b1220" stroke-width="25"/><path d="m756 438 27 55 55 27-55 27-27 55-27-55-55-27 55-27Zm-50 272 15 31 31 15-31 15-15 31-15-31-31-15 31-15Z" fill="#f1f7ff"/></svg>''', encoding='utf-8')
# Installer artwork is generated from the same icon.
small = image.convert('RGB').resize((55, 55), Image.Resampling.LANCZOS)
small.save(assets / 'wizard-small.bmp')
banner = Image.new('RGB', (164, 314), '#0b1220')
banner.paste(image.convert('RGB').resize((120, 120), Image.Resampling.LANCZOS), (22, 72))
ImageDraw.Draw(banner).text((44, 214), 'CleanTemp', fill='#4dd4c7')
banner.save(assets / 'wizard-large.bmp')
