#!/usr/bin/env python
"""Push output/probe_cluster_enclosure.fs to the Onshape document (Feature Studio) and insert/refresh the custom feature
in Part Studio 1.  Every call here spends the user's yearly Onshape API allocation: a full push is ~7 requests,
a refresh of an existing feature ~5.  Run only after generate.py has produced geometry worth looking at.

Usage:  source ~/.zshrc; python push.py [--dry]
"""
import os, sys, json, time
from pathlib import Path
import requests

DID, WID = "937c54b34f0ccb974f37f949", "275b479cd4996a16dce317f4"
PS = "c10029ec19783bb5bae02ce9"                 # Part Studio 1
FS_NAME = "Cluster enclosure FeatureScript"
FEATURE_TYPE, FEATURE_NAME = "probeClusterEnclosure", "Probe cluster enclosure"
API = "https://cad.onshape.com/api/v10"
HERE = Path(__file__).parent; STATE = HERE / "output" / "onshape_ids.json"
CALLS = 0

def api(method, path, body=None):
    global CALLS; CALLS += 1
    auth = (os.environ["ONSHAPE_ACCESS_KEY"], os.environ["ONSHAPE_SECRET_KEY"])
    for attempt in range(4):
        r = requests.request(method, API + path, json=body, auth=auth, headers={"Accept": "application/json;charset=UTF-8; qs=0.09"}, timeout=180)
        if r.status_code != 429: break
        print(f"  429 rate limited, waiting {30 * (attempt + 1)} s"); time.sleep(30 * (attempt + 1))
    if r.status_code >= 400: raise SystemExit(f"{method} {path} -> {r.status_code}: {r.text[:600]}")
    return r.json() if r.content.strip() else {}

def main():
    dry = "--dry" in sys.argv
    code = (HERE / "output" / "probe_cluster_enclosure.fs").read_text()
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    if dry: print(f"would push {len(code)//1024} kB; state={state}"); return
    fsid = state.get("fsid")
    if not fsid:
        fs = api("POST", f"/featurestudios/d/{DID}/w/{WID}", {"name": FS_NAME})
        fsid = fs["id"]; state["fsid"] = fsid; STATE.write_text(json.dumps(state, indent=1))
        print("created Feature Studio", fsid)
    api("POST", f"/featurestudios/d/{DID}/w/{WID}/e/{fsid}", {"contents": code})
    specs = api("GET", f"/featurestudios/d/{DID}/w/{WID}/e/{fsid}/featurespecs")
    names = [s.get("featureType") for s in specs.get("featureSpecs", [])]
    if FEATURE_TYPE not in names:
        raise SystemExit("FeatureScript did not compile:\n" + json.dumps(specs, indent=1)[:3000])
    print("compiled OK; feature types:", names)
    feats = api("GET", f"/partstudios/d/{DID}/w/{WID}/e/{PS}/features")
    existing = [f for f in feats["features"] if f.get("featureType") == FEATURE_TYPE]
    mv = api("GET", f"/documents/d/{DID}/w/{WID}/currentmicroversion")["microversion"]
    params = [{"btType": "BTMParameterBoolean-144", "parameterId": p, "value": True} for p in ("buildShell", "buildSpine", "buildKeel", "buildCoupon")]
    if not existing:
        feat = {"btType": "BTMFeature-134", "featureType": FEATURE_TYPE, "name": FEATURE_NAME, "namespace": f"e{fsid}::m{mv}", "parameters": params}
        api("POST", f"/partstudios/d/{DID}/w/{WID}/e/{PS}/features", {"feature": feat}); print("inserted feature")
    else:   # replace: delete + insert pins the namespace to the new Feature Studio microversion (an in-place update returns 'Feature does not match')
        for f in existing: api("DELETE", f"/partstudios/d/{DID}/w/{WID}/e/{PS}/features/featureid/{f['featureId']}")
        feat = {"btType": "BTMFeature-134", "featureType": FEATURE_TYPE, "name": FEATURE_NAME, "namespace": f"e{fsid}::m{mv}", "parameters": params}
        api("POST", f"/partstudios/d/{DID}/w/{WID}/e/{PS}/features", {"feature": feat}); print("replaced feature")
    st = {}
    for _ in range(30):
        feats = api("GET", f"/partstudios/d/{DID}/w/{WID}/e/{PS}/features")
        st = {f["name"]: feats["featureStates"].get(f["featureId"], {}) for f in feats["features"]}
        if all(v.get("featureStatus") in ("OK", "WARNING") for v in st.values()): break
        if any(v.get("featureStatus") == "ERROR" for v in st.values()): break
        time.sleep(4)
    for k, v in st.items(): print(f"  feature {k!r}: {v.get('featureStatus')}  {v.get('message', '') or ''}")
    if all(v.get("featureStatus") in ("OK", "WARNING") for v in st.values()):
        parts = api("GET", f"/parts/d/{DID}/w/{WID}/e/{PS}")
        for p in parts: print(f"  part {p['name']:<14} id={p['partId']}")
    if all(v.get("featureStatus") in ("OK", "WARNING") for v in st.values()) and "--no-assembly" not in sys.argv:
        rebuild_assembly(state)
    print(f"API requests this run: {CALLS}")
    print(f"open: https://cad.onshape.com/documents/{DID}/w/{WID}/e/{state.get('asm', PS)}")

MESH_PS = "177864c843a60c8c5b179426"   # imported scan mesh (42 closed + 58 open mesh bodies)

def rebuild_assembly(state):
    """Regeneration gives the parts new IDs, which breaks existing assembly instances: delete the assembly and rebuild it
    (1 delete + 1 create + 3 inserts). The scan mesh needs PARTS and SURFACES inserts (most of it is open surface)."""
    old = state.get("asm")
    if old: api("DELETE", f"/elements/d/{DID}/w/{WID}/e/{old}")
    asm = api("POST", f"/assemblies/d/{DID}/w/{WID}", {"name": "Enclosure assembly"})["id"]
    state["asm"] = asm; STATE.write_text(json.dumps(state, indent=1))
    for eid, types in ((PS, ["PARTS"]), (MESH_PS, ["PARTS"]), (MESH_PS, ["SURFACES"])):
        api("POST", f"/assemblies/d/{DID}/w/{WID}/e/{asm}/instances", {"documentId": DID, "elementId": eid, "isWholePartStudio": True, "includePartTypes": types})
    print("assembly rebuilt:", asm)

if __name__ == "__main__":
    main()
