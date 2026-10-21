"""Bambu Studio offline slicing, with fully resolved installed factory presets.
The resulting G-code is verification output only and is not a print deliverable.
"""
from pathlib import Path
import json,subprocess
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'design/output';D=OUT/'slicer-check'
BASE=Path('/Applications/BambuStudio.app/Contents/Resources/profiles/BBL')
APP='/Applications/BambuStudio.app/Contents/MacOS/BambuStudio'
index={p.stem:p for p in BASE.rglob('*.json')}
def resolve(name,seen=()):
 if name in seen:raise ValueError('Profile cycle')
 obj=json.loads(index[name].read_text());result={}
 parent=obj.get('inherits')
 if parent:result.update(resolve(parent,seen+(name,)))
 for inc in obj.get('include',[]):result.update(resolve(inc,seen+(name,)))
 result.update(obj);result.pop('inherits',None);result.pop('include',None)
 return result
machine=resolve('Bambu Lab P1S 0.4 nozzle')
process=resolve('0.20mm Standard @BBL X1C')
process.update(wall_loops='6',top_shell_layers='6',bottom_shell_layers='6',sparse_infill_density='40%',sparse_infill_pattern='gyroid',curr_bed_type='Textured PEI Plate',brim_width='5',brim_type='outer_only',outer_wall_speed=['60','60'],inner_wall_speed=['100','100'])
filament=resolve('Bambu ASA @BBL X1C 0.4 nozzle')
D.mkdir(exist_ok=True)
for name,obj in [('machine',machine),('process',process),('filament',filament)]:
 (D/(name+'.json')).write_text(json.dumps(obj,indent=2))
assert machine['printable_area']==['0x0','256x0','256x256','0x256'],machine.get('printable_area')
summary={}
for plate in ['01_side_plates','02_cage_clamps','03_tab_adapters','00_fit_check']:
 dest=D/plate;dest.mkdir(exist_ok=True)
 proc=process.copy();proc['enable_support']='1' if plate in ['03_tab_adapters','00_fit_check'] else '0'
 proc.update(support_type='tree(auto)',support_on_build_plate_only='1')
 (dest/'process.json').write_text(json.dumps(proc,indent=2))
 args=[APP,'--datadir',str(ROOT/'design/.slicer'),'--load-settings',str(D/'machine.json')+';'+str(dest/'process.json'),'--load-filaments',str(D/'filament.json'),
       '--arrange','0','--ensure-on-bed','--orient','0','--slice','0','--export-settings',str(dest/'effective.json'),'--outputdir',str(dest),str(OUT/'plates'/(plate+'.3mf'))]
 run=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 (dest/'slice.log').write_text(run.stdout)
 result=json.loads((dest/'result.json').read_text()) if (dest/'result.json').exists() else {'return_code':run.returncode,'error_string':run.stdout[-1500:]}
 summary[plate]=result
 print(plate,result.get('return_code'),result.get('error_string'),flush=True)
(OUT/'slicer_verification.json').write_text(json.dumps(summary,indent=2))
