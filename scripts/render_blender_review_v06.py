"""Queue deterministic multi-view renders in the active Blender instance.
Run through Blender MCP after model/blender_dragon_v06.py. Rendering is split into
timer jobs so the MCP call can return before the batch completes.
"""
import bpy
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'renders/blender-v06'
SCENE=bpy.data.scenes['Dragon • Puffy Hoops 06']
VIEWS=['hero','opposite','top','side_a','side_b','head_end','return_end','junction','slide_detail']

def queue_review(views=None):
    pending=list(views or VIEWS)
    completed=[name for name in VIEWS if name not in pending and (OUTPUT/(name+'.png')).exists()]
    OUTPUT.mkdir(parents=True,exist_ok=True)
    SCENE.render.resolution_x=1400
    SCENE.render.resolution_y=1050
    SCENE.cycles.samples=48
    status=OUTPUT/'render-status.json'
    status.write_text(json.dumps({'status':'queued','remaining':pending}))
    def step():
        try:
            name=pending.pop(0)
            SCENE.camera=bpy.data.objects['VIEW_'+name]
            SCENE.render.filepath=str(OUTPUT/(name+'.png'))
            bpy.ops.render.render(write_still=True,scene=SCENE.name)
            completed.append(name)
            status.write_text(json.dumps({'status':'rendering' if pending else 'complete','completed':completed,'remaining':pending},indent=2))
            if pending:return .2
            SCENE.camera=bpy.data.objects['VIEW_hero']
            bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'model/blender/dragon-puffy-hoops-v06.blend'))
        except Exception as e:
            status.write_text(json.dumps({'status':'failed','error':str(e),'completed':completed,'remaining':pending},indent=2))
        return None
    bpy.app.timers.register(step,first_interval=.2)
    print('Queued review angles: '+', '.join(pending))

if __name__=='__main__':queue_review()
