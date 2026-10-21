"""Global interference and transform/hash audit on delivered binary STL meshes."""
from pathlib import Path
import sys,json,hashlib
import numpy as np,trimesh
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from model.printkit.common import from_mesh,Part
from scripts.build_print_kit import collision_check
OUT=ROOT/'exports/dragon-pla-kit-v03'
m=json.loads((OUT/'manifest.json').read_text());parts=[];records=[]
for p in m['parts']:
 path=OUT/p['file'];mesh=trimesh.load(path,force='mesh',process=True)
 rotation=np.asarray(p['print_rotation_world_to_bed']);origin=np.asarray(p['print_minimum_before_translation_mm'])
 vertices=(mesh.vertices+origin)@rotation
 restored=np.load(OUT/'work/assembly'/(p['name']+'.npz'))
 assert np.array_equal(mesh.faces,restored['faces']) and np.max(abs(vertices-restored['vertices']))<1e-10,p['name']
 solid=from_mesh(vertices,mesh.faces)
 assert mesh.is_watertight and mesh.volume>0 and len(solid.decompose())==1,p['name']
 if not p['test']:parts.append(Part(p['name'],p['color'],solid))
 records.append({'name':p['name'],'file':p['file'],'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'watertight':True,'components':1,'transform_verified':True})
collisions=collision_check(parts)
report={'status':'passed'if not collisions else'failed','individual_files':len(records),'production_parts':len(parts),'pair_intersection_reporting_threshold_mm3':.015,'inter_part_overlaps':collisions,'parts':records,'physical_fit':'not tested'}
(OUT/'validation/export-v03-audit.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items()if k!='parts'},indent=2))
assert not collisions
