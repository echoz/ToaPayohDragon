"""Create printable plate identification maps after the final kit manifest exists.

Uses the exported STL dimensions and packing transforms, not a guessed layout.
No mesh edits, slicing, browser operations, or source-model modifications occur.
"""
from pathlib import Path
import html
import json
import sys
from urllib.parse import quote

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
OUT=ROOT/'exports/dragon-pla-kit-v03'


def esc(value):return html.escape(str(value),quote=True)
def href(path):return quote(str(path),safe='/._-')
def number(value):return f'{float(value):.2f}'


def plate_svg(plate,parts,colours):
    chunks=['<svg viewBox="0 0 284 286" role="img" aria-label="'+esc(plate['name'])+' print bed footprints" xmlns="http://www.w3.org/2000/svg">',
            '<rect x="12" y="12" width="256" height="256" rx="3" fill="#fff" stroke="#64748b" stroke-width=".8"/>',
            '<rect x="37" y="23" width="220" height="215" fill="#f5f7f9" stroke="#b6c1ce" stroke-dasharray="2 2" stroke-width=".5"/>']
    for value in (0,64,128,192,256):
        x=12+value;y=268-value
        chunks.append(f'<text x="{x}" y="278" text-anchor="middle" font-size="4.4" fill="#526273">{value}</text>')
        chunks.append(f'<text x="8" y="{y+1.5}" text-anchor="end" font-size="4.4" fill="#526273">{value}</text>')
    chunks.append('<text x="140" y="285" text-anchor="middle" font-size="4.8" fill="#526273">FRONT • X / Y in millimetres • bed 256 × 256</text>')
    for index,placed in enumerate(plate['parts'],1):
        part=parts[placed['name']]
        w,h=part['dimensions_mm'][:2]
        if placed.get('rotate90'):w,h=h,w
        x0,y0=placed['origin_mm'][:2]
        if x0 < -0.05 or y0 < -0.05 or x0+w>256.05 or y0+h>256.05:
            raise ValueError(f"Out-of-bed footprint: {part['name']}")
        x=12+x0;y=268-y0-h;cx=x+w/2;cy=y+h/2
        fill=colours[part['color']]
        label=f"{index}. {part['name']}. {w:.2f} × {h:.2f} mm footprint."
        chunks += [f'<a href="{href(part["file"])}"><title>{esc(label)}</title>',
                   f'<rect x="{number(x)}" y="{number(y)}" width="{number(w)}" height="{number(h)}" fill="{fill}" fill-opacity=".7" stroke="#334155" stroke-width=".6"/>',
                   f'<circle cx="{number(cx)}" cy="{number(cy)}" r="4.2" fill="white" fill-opacity=".94" stroke="#334155" stroke-width=".35"/>',
                   f'<text x="{number(cx)}" y="{number(cy+1.85)}" text-anchor="middle" font-size="5.4" font-weight="700" fill="#172334">{index}</text></a>']
    return ''.join(chunks)+'</svg>'


def route_svg(manifest):
    from model.printkit.common import sample_route,route_path,F
    from model.printkit.body import CUTS,COLORS
    scale=2.55;ox=360;oy=340
    def xy(p):return ox+float(p[0])*scale,oy-float(p[1])*scale
    def path_d(points):return ' '.join(('M' if i==0 else 'L')+f'{xy(p)[0]:.2f},{xy(p)[1]:.2f}' for i,p in enumerate(points))
    chunks=['<svg viewBox="0 0 760 530" role="img" aria-label="Actual body route with numbered hoops, piers and beam joints" xmlns="http://www.w3.org/2000/svg">',
            '<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#264e70"/></marker></defs>']
    x0,y0=xy([-116*F,102*F,0]);x1,y1=xy([126*F,-61*F,0])
    chunks.append(f'<rect x="{x0:.2f}" y="{y0:.2f}" width="{x1-x0:.2f}" height="{y1-y0:.2f}" rx="38" fill="#faf6eb" stroke="#cdbda5" stroke-width="2"/>')
    chunks.append('<text x="66" y="95" class="map-title">ASSEMBLED TOP VIEW</text><text x="66" y="115" class="map-small">Actual route • hoops numbered head → tail</text>')
    # Light positional head/slide outlines give context, not fabrication templates.
    floor=[[61.3*F,-28*F,0],[61.3*F,28*F,0],[96*F,9.3*F,0],[96*F,-9.3*F,0]]
    chunks.append(f'<path d="{path_d(floor)} Z" fill="#f6d2bf" stroke="#b4775f" stroke-width="1.5"/>')
    for points in [ [[62*F,-23*F,0],[52*F,-27*F,0],[9*F,-43*F,0],[-8*F,-47*F,0]],
                    [[62*F,21*F,0],[55*F,28*F,0],[24*F,63*F,0],[6*F,88*F,0]] ]:
        chunks.append(f'<path d="{path_d(points)}" fill="none" stroke="#e2c6b1" stroke-width="17" stroke-linecap="round"/>')
    chunks.append('<text x="600" y="342" text-anchor="middle" class="map-title">HEAD</text>')
    chunks.append(f'<path d="{path_d(route_path())}" fill="none" stroke="#a8bed0" stroke-width="17" stroke-linecap="round"/>')
    chunks.append(f'<path d="{path_d(route_path())}" fill="none" stroke="#446a85" stroke-width="2"/>')
    for fraction in (.08,.34,.59,.85):
        pts=[sample_route(fraction-.016)[0],sample_route(fraction+.016)[0]]
        chunks.append(f'<path d="{path_d(pts)}" fill="none" stroke="#264e70" stroke-width="2" marker-end="url(#arrow)"/>')
    for index,fraction in enumerate(CUTS[1:-1],1):
        p,t,n=sample_route(fraction);a=p-n*8;b=p+n*8;q=p+n*18
        if index==3:q=p-n*22
        x,y=xy(q)
        chunks.append(f'<path d="{path_d([a,b])}" stroke="#9d4050" stroke-width="2" stroke-dasharray="3 2"/>')
        chunks.append(f'<text x="{x:.2f}" y="{y:.2f}" text-anchor="middle" class="joint-label">B{index} / B{index+1}</text>')
    piers=manifest.get('interfaces',{}).get('piers',{}).get('piers',[])
    if not piers:piers=[{'pier':i,'fraction':f} for i,f in enumerate([2/17,5/17,8/17,12/17,15/17],1)]
    for pier in piers:
        p,t,n=sample_route(pier['fraction']);q=p-n*18;x,y=xy(q)
        chunks.append(f'<path d="{path_d([p,q])}" stroke="#777164" stroke-width="1"/>')
        chunks.append(f'<rect x="{x-14:.2f}" y="{y-10:.2f}" width="28" height="20" rx="4" fill="#fff" stroke="#958671"/>')
        chunks.append(f'<text x="{x:.2f}" y="{y+4:.2f}" text-anchor="middle" class="pier-label">P{pier["pier"]}</text>')
    records={p['name']:p for p in manifest['parts']}
    for index in range(18):
        p,t,n=sample_route(index/17);x,y=xy(p);name=f'body_hoop_{index+1:02}'
        record=records.get(name,{});colour=record.get('color',COLORS[index]);colourhex=manifest['colors'][colour]
        link=href(record.get('file',f'parts/{colour}/{name}.stl'))
        chunks += [f'<a href="{link}"><title>{esc(name)} · {esc(colour)}</title>',
                   f'<circle cx="{x:.2f}" cy="{y:.2f}" r="11" fill="{colourhex}" stroke="#26384b" stroke-width="1.3"/>',
                   f'<text x="{x:.2f}" y="{y+4:.2f}" text-anchor="middle" class="hoop-label">{index+1}</text></a>']
    p,t,n=sample_route(1);x,y=xy(p+n*22)
    chunks.append(f'<text x="{x:.2f}" y="{y:.2f}" text-anchor="middle" class="map-title">TAIL</text>')
    chunks.append('<text x="65" y="481" class="map-small">P1–P5 = piers · B1/B2 etc. = beam joints · click a hoop to open its STL</text>')
    return ''.join(chunks)+'</svg>'


STYLE='''
:root{color-scheme:light;font-family:Arial,Helvetica,sans-serif;color:#243347;background:#eef1f3;font-size:15px}*{box-sizing:border-box}body{margin:0}main{max-width:1180px;margin:auto;padding:30px 24px 60px}h1{font-size:30px;letter-spacing:-.6px;margin:0 0 10px}h2{font-size:18px;margin:0 0 8px}p{line-height:1.5;margin:8px 0 15px}a{color:#215b83;text-decoration:none}a:hover{text-decoration:underline}code{font-size:.9em}header{margin-bottom:24px}.muted{color:#64748b}.summary{display:flex;flex-wrap:wrap;gap:10px;margin:16px 0}.badge{font-size:12px;background:#fff;border:1px solid #d5dce2;padding:6px 10px;border-radius:7px}.legend{display:flex;gap:12px;flex-wrap:wrap}.swatch{display:inline-block;width:12px;height:12px;border:1px solid #81909e;border-radius:3px;vertical-align:-1px;margin-right:5px}.card{background:#fff;border:1px solid #d5dce2;border-radius:12px;padding:20px;break-inside:avoid}.route{display:grid;grid-template-columns:2fr 1fr;align-items:center;gap:22px;margin-bottom:25px}.route svg{width:100%;height:auto}.map-title{font:700 14px Arial;fill:#2e3d4c}.map-small{font:12px Arial;fill:#637080}.joint-label{font:700 12px Arial;fill:#9d4050;paint-order:stroke;stroke:#faf6eb;stroke-width:4px}.pier-label{font:700 11px Arial;fill:#4a453d}.hoop-label{font:700 11px Arial;fill:#152b3e;paint-order:stroke;stroke:#ffffff88;stroke-width:2px}.route table{font-size:12px}table{width:100%;border-collapse:collapse}th{text-align:left;color:#64748b;font-size:11px;letter-spacing:.02em;border-bottom:1px solid #ccd6de;padding:7px 5px}td{border-bottom:1px solid #e9edf1;padding:7px 5px;vertical-align:top;font-size:12px}td.file{overflow-wrap:anywhere}td.idx{width:24px;font-weight:bold}td.size{white-space:nowrap;text-align:right;font-variant-numeric:tabular-nums;color:#607185}.plates{display:grid;grid-template-columns:1fr 1fr;gap:20px}.plate header{margin-bottom:4px}.plate h2{font-size:16px;overflow-wrap:anywhere}.plate .sub{font-size:12px}.plate svg{display:block;width:100%;max-height:460px;margin:4px auto 10px}.footnote{font-size:11px;color:#697785;margin:10px 0 0}.section-title{margin:30px 0 15px}.test{border-top:4px solid #b78035}.no-print{cursor:pointer;border:0;background:#234f70;color:#fff;border-radius:7px;padding:10px 16px;font-weight:bold}footer{margin-top:22px;font-size:12px;color:#697785}
@media(max-width:750px){main{padding:22px 14px}.plates,.route{grid-template-columns:1fr}}
@media print{@page{size:A4 portrait;margin:10mm}:root{font-size:10pt;background:#fff}main{padding:0;max-width:none}h1{font-size:21pt}.no-print{display:none}.summary{gap:5px}.badge{font-size:8pt;padding:4px 6px}.card{border-radius:0;padding:10px}.route{grid-template-columns:1fr;margin:0 0 12px;break-after:page}.route svg{max-height:150mm}.route>div:last-child{display:grid;grid-template-columns:1fr 1fr;gap:12px}.route>div:last-child h2{grid-column:1/-1}.plates{display:block}.plate{break-after:page;border:0}.plate svg{height:125mm;max-height:none}.plate table{font-size:8pt}.plate td{padding:4px;font-size:8pt}.plate h2{font-size:12pt}.section-title{display:none}.footnote,footer{font-size:8pt}a{color:inherit}a[href]::after{content:none}}
'''


def build_html(manifest):
    parts={p['name']:p for p in manifest['parts']};colours=manifest['colors']
    plates=sorted(manifest['plates'],key=lambda p:(not p.get('test',False),p['color'],p['supports_required'],p['name']))
    cards=[]
    for plate in plates:
        rows=[]
        for index,placed in enumerate(plate['parts'],1):
            part=parts[placed['name']];w,h,z=part['dimensions_mm']
            if placed.get('rotate90'):w,h=h,w
            rows.append(f'<tr><td class="idx">{index}</td><td class="file"><a href="{href(part["file"])}">{esc(Path(part["file"]).name)}</a></td><td class="size">{w:.1f} × {h:.1f} × {z:.1f}</td></tr>')
        support='Supports required' if plate['supports_required'] else 'No supports specified'
        purpose='OPTIONAL ASSEMBLY CRADLES' if plate.get('purpose')=='assembly_jig' else ('FIT SAMPLES · PRINT FIRST' if plate.get('test') else 'PRODUCTION PARTS')
        cards.append(f'''<article class="card plate {'test' if plate.get('test') else ''}"><header><h2><a href="{href(plate['file'])}">{esc(plate['name'])}.stl</a></h2><p class="sub"><span class="swatch" style="background:{esc(colours[plate['color']])}"></span>{esc(plate['color'].title())} PLA · {support} · {len(plate['parts'])} pieces<br><span class="muted">{purpose}</span></p></header>{plate_svg(plate,parts,colours)}<table><thead><tr><th>#</th><th>Individual STL filename</th><th style="text-align:right">Packed W × D × H mm</th></tr></thead><tbody>{''.join(rows)}</tbody></table><p class="footnote">Boxes show occupied XY bounds, not mesh silhouettes. Numbered locations match this plate STL; re-arranging parts in the slicer changes the map. Part dimensions include packing rotation. Keep STL scale at 100%.</p></article>''')
    slicer_status=str(manifest.get('validation',{}).get('slicer_status','pending'))
    if slicer_status.startswith('passed_all_'):
        slicer_note=f'All {len(plates)} plates passed slicer validation. Physical printing and joint fit remain untested.'
    elif slicer_status.lower() in ('pending','untested','unknown'):
        slicer_note='The full kit still awaits completed slicer validation.'
    else:
        slicer_note='Slicer validation status: '+slicer_status.replace('_',' ')+'.'
    if str(manifest.get('validation',{}).get('tolerance_audit','')).startswith('changes_required'):
        slicer_note='FULL PRINT ON HOLD: the tolerance audit found fit and assembly defects. Read TOLERANCE-AUDIT.md before production printing. '+slicer_note
    legend=''.join(f'<span><i class="swatch" style="background:{esc(value)}"></i>{esc(name.title())}</span>' for name,value in colours.items())
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Dragon PLA kit · plate and assembly maps</title><style>{STYLE}</style></head><body><main><header><h1>Dragon PLA kit: find every piece</h1><p>Print identification maps for the Bambu Lab X1 Carbon, 0.4 mm nozzle and PLA. Each numbered plate box links to its individual STL; each plate heading links to the packed STL.</p><div class="summary"><span class="badge">{manifest['part_count']} model parts</span><span class="badge">{manifest['fit_sample_count']} fit samples · {manifest['assembly_jig_count']} assembly cradles</span><span class="badge">{manifest['plate_count']} colour plates</span><span class="badge">Millimetres · 100% scale</span></div><div class="legend">{legend}</div><p><button class="no-print" onclick="window.print()">Print these maps</button> <a href="README.md">Assembly and printing guide</a> · <a href="FIT-TESTS.md">Fit samples</a> · <a href="preview/opposite.png">Assembled preview</a> · <a href="preview/tail_detail.png">Tail detail</a> · <a href="manifest.json">Open kit manifest</a></p><p class="muted">{esc(slicer_note)} Read the guide for the latest checks and print the fit test first.</p></header><section class="card route"><div>{route_svg(manifest)}</div><div><h2>Match the body by number</h2><p>Hoop 01 sits next to the head. Stations 16–18 are open U-rungs; station 18 sits on the low tail landing. Follow the arrows around the return. Keep the hoop numbers in this order.</p><table><thead><tr><th>Beam module</th><th>Hoops</th></tr></thead><tbody><tr><td>B1 · section 01</td><td>01–05</td></tr><tr><td>B2 · section 02</td><td>06–10</td></tr><tr><td>B3 · section 03</td><td>11–14</td></tr><tr><td>B4 · section 04</td><td>15–17</td></tr></tbody></table><p class="muted">P1–P5 identify the five piers, in head-to-tail order. The four rail tracks each use sections 01–04 in this same direction. The pale head and slide outlines only provide position context.</p><p class="muted">Use the kit assembly guide for glue and joint instructions. The map identifies parts; it is not a full-size cutting template.</p></div></section><h2 class="section-title">Plate identification</h2><section class="plates">{''.join(cards)}</section><footer>{esc(slicer_note)} Generated from manifest.json after export. Footprints come from the actual exported STL dimensions and recorded packing origins/rotations. Print supports and clearances still require physical verification.</footer></main></body></html>'''


def main():
    manifest_path=OUT/'manifest.json'
    if not manifest_path.is_file():
        print('Waiting for exports/dragon-pla-kit-v03/manifest.json; no map generated.')
        return 0
    manifest=json.loads(manifest_path.read_text())
    for record in manifest['parts']+manifest['plates']:
        if not (OUT/record['file']).is_file():
            raise FileNotFoundError(f"Manifest references missing STL: {record['file']}")
    document=build_html(manifest)
    dest=OUT/'assembly-map.html';dest.write_text(document)
    print(f'Created {dest} ({len(manifest["plates"])} plate maps).')
    return 0


if __name__=='__main__':raise SystemExit(main())
