"""Independent overhang/layer screening of every actual v03 STL."""
from pathlib import Path
import sys,json,hashlib,concurrent.futures,math
import numpy as np,trimesh
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.audit_tail_v02 import audit_part,selected
OUT=ROOT/'exports/dragon-pla-kit-v03'

def check(p):
 r=audit_part(p,OUT,.16,.10,.02)
 # STL float32 rounding perturbs exactly 45-degree chamfer normals by ~.001°.
 # Retain raw evidence but allow .01° numerically; layer/island checks unchanged.
 mesh=trimesh.load(OUT/p['file'],force='mesh',process=True)
 above=np.max(mesh.triangles[:,:,2],axis=1)>mesh.bounds[0,2]+.10
 mask=above & (mesh.face_normals[:,2] < -math.sin(math.radians(45.01)))
 r['face_angle_numerical_tolerance_deg']=.01
 r['downward_face_area_with_numerical_tolerance_mm2']=float(mesh.area_faces[mask].sum())
 r['unresolved_support_free_flag']=p['supports']=='none' and (r['flagged_layer_count']>0 or r['downward_face_area_with_numerical_tolerance_mm2']>.02)
 return r

def main():
 m=json.loads((OUT/'manifest.json').read_text());results=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:
  for r in pool.map(check,m['parts']):
   print(r['part'],r['flagged_layer_count'],'layers',r['unresolved_support_free_flag'],'unresolved',flush=True)
   results.append(r)
 report={'manifest':'manifest.json','manifest_sha256_at_audit':hashlib.sha256((OUT/'manifest.json').read_bytes()).hexdigest(),
  'method':{'geometry':'Actual binary STL in its supplied print orientation','layer_height_mm':.16,'first_sample_mm':.10,'area_threshold_mm2':.02,'growth_limit_degrees_from_vertical':45,
   'face_angle_numerical_tolerance_deg':.01,'limits':'Geometric screen only; supported pieces need slicer toolpaths and support removal. Does not prove extrusion, fit or strength.'},
  'part_count':len(results),'unresolved_support_free_parts':[r['part']for r in results if r['unresolved_support_free_flag']],'parts':results}
 (OUT/'validation/print-v03-audit.json').write_text(json.dumps(report,indent=2))
 tail=[r for r in results if selected(r['part'],[])]
 tail_report=dict(report,part_count=len(tail),parts=tail,unresolved_support_free_parts=[r['part']for r in tail if r['unresolved_support_free_flag']])
 (OUT/'validation/tail-v03-print-audit.json').write_text(json.dumps(tail_report,indent=2))
 print('UNRESOLVED',report['unresolved_support_free_parts'],flush=True)
if __name__=='__main__':main()
