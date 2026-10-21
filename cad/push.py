#!/usr/bin/env python
"""Push output/probe_cluster_enclosure.fs to the Onshape document (Feature Studio) and insert/refresh the custom feature
in Part Studio 1.  Every call here spends the user's yearly Onshape API allocation: a full push is ~7 requests,
a refresh of an existing feature ~5.  Run only after generate.py has produced geometry worth looking at.

Usage:  source ~/.zshrc; python push.py [--dry] [--cradle | --mount-only | --sidemount] [--no-assembly]
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
    mount_code = (HERE / "output" / "cluster_mount.fs").read_text() if (HERE / "output" / "cluster_mount.fs").exists() else ""
    cradle_code = (HERE / "output" / "cluster_cradle.fs").read_text() if (HERE / "output" / "cluster_cradle.fs").exists() else ""
    code = code + "\n" + mount_code + "\n" + cradle_code
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    if dry: print(f"would push {len(code)//1024} kB; state={state}"); return
    if "--sidemount" in sys.argv:
        # side mount: no FeatureScript at all. Upload the car-frame STEP as a new Part Studio and rebuild the
        # "Side mount system" assembly (~14 requests)
        push_sidemount(state)
        if "--no-assembly" not in sys.argv: rebuild_sidemount_assembly(state)
        print(f"API requests this run: {CALLS}"); return
    fsid = state.get("fsid")
    if not fsid:
        fs = api("POST", f"/featurestudios/d/{DID}/w/{WID}", {"name": FS_NAME})
        fsid = fs["id"]; state["fsid"] = fsid; STATE.write_text(json.dumps(state, indent=1))
        print("created Feature Studio", fsid)
    api("POST", f"/featurestudios/d/{DID}/w/{WID}/e/{fsid}", {"contents": code})
    specs = api("GET", f"/featurestudios/d/{DID}/w/{WID}/e/{fsid}/featurespecs")
    names = [s.get("featureType") for s in specs.get("featureSpecs", [])]
    print("feature types compiled:", names)
    if FEATURE_TYPE not in names:
        raise SystemExit("FeatureScript did not compile:\n" + json.dumps(specs, indent=1)[:3000])
    print("compiled OK; feature types:", names)
    if "--cradle" in sys.argv:
        # cradle only: upload the FS (enclosure + mount features untouched, pinned), insert/replace the cradle feature in its own
        # Part Studio and rebuild only the "Cradle system" assembly (~20 requests)
        mv = api("GET", f"/documents/d/{DID}/w/{WID}/currentmicroversion")["microversion"]
        push_cradle(state, fsid, mv)
        if "--no-assembly" not in sys.argv: rebuild_cradle_assembly(state)
        print(f"API requests this run: {CALLS}"); return
    if "--mount-only" in sys.argv:
        # only the mount changed: leave the enclosure feature pinned to its current microversion (its parts and the
        # enclosure assembly stay valid), re-insert the mount feature and rebuild just the full-system assembly (~20 requests)
        mv = api("GET", f"/documents/d/{DID}/w/{WID}/currentmicroversion")["microversion"]
        push_mount(state, fsid, mv)
        if "--no-assembly" not in sys.argv and state.get("mount_ps") and state.get("cage_ps"): rebuild_full_assembly(state)
        print(f"API requests this run: {CALLS}"); return
    feats = api("GET", f"/partstudios/d/{DID}/w/{WID}/e/{PS}/features")
    existing = [f for f in feats["features"] if f.get("featureType") == FEATURE_TYPE]
    mv = api("GET", f"/documents/d/{DID}/w/{WID}/currentmicroversion")["microversion"]
    params = [{"btType": "BTMParameterBoolean-144", "parameterId": p, "value": True} for p in ("buildShell", "buildSpine", "buildKeel", "buildCoupon", "buildFeet")]
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
    if mount_code and "clusterCageMount" in names:
        push_mount(state, fsid, mv)
    if all(v.get("featureStatus") in ("OK", "WARNING") for v in st.values()) and "--no-assembly" not in sys.argv:
        rebuild_assembly(state)
        if state.get("mount_ps") and state.get("cage_ps"):
            rebuild_full_assembly(state)
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


MOUNT_TYPE, MOUNT_NAME = "clusterCageMount", "Cluster cage mount"

def push_mount(state, fsid, mv):
    """Mount feature lives in its own Part Studio (car frame). Same Feature Studio; delete + re-insert to pin the microversion."""
    ps = state.get("mount_ps")
    if not ps:
        ps = api("POST", f"/partstudios/d/{DID}/w/{WID}", {"name": "Mount (car frame)"})["id"]; state["mount_ps"] = ps; STATE.write_text(json.dumps(state, indent=1)); print("created Mount Part Studio", ps)
    feats = api("GET", f"/partstudios/d/{DID}/w/{WID}/e/{ps}/features")
    for f in feats["features"]:
        if f.get("featureType") == MOUNT_TYPE: api("DELETE", f"/partstudios/d/{DID}/w/{WID}/e/{ps}/features/featureid/{f['featureId']}")
    params = [{"btType": "BTMParameterBoolean-144", "parameterId": p, "value": True} for p in ("buildBar", "buildArms")]
    api("POST", f"/partstudios/d/{DID}/w/{WID}/e/{ps}/features", {"feature": {"btType": "BTMFeature-134", "featureType": MOUNT_TYPE, "name": MOUNT_NAME, "namespace": f"e{fsid}::m{mv}", "parameters": params}})
    for _ in range(20):
        feats = api("GET", f"/partstudios/d/{DID}/w/{WID}/e/{ps}/features")
        stt = {f["name"]: feats["featureStates"].get(f["featureId"], {}).get("featureStatus") for f in feats["features"]}
        if all(v in ("OK", "WARNING", "ERROR") for v in stt.values()): break
        time.sleep(4)
    print("  mount feature:", stt)
    for p in api("GET", f"/parts/d/{DID}/w/{WID}/e/{ps}"): print(f"  mount part {p['name']}")

CRADLE_TYPE, CRADLE_NAME = "clusterCradle", "Cluster cradle"

def push_cradle(state, fsid, mv):
    ps = state.get("cradle_ps")
    if not ps:
        ps = api("POST", f"/partstudios/d/{DID}/w/{WID}", {"name": "Cradle (scan frame)"})["id"]; state["cradle_ps"] = ps; STATE.write_text(json.dumps(state, indent=1)); print("created Cradle Part Studio", ps)
    feats = api("GET", f"/partstudios/d/{DID}/w/{WID}/e/{ps}/features")
    for f in feats["features"]:
        if f.get("featureType") == CRADLE_TYPE: api("DELETE", f"/partstudios/d/{DID}/w/{WID}/e/{ps}/features/featureid/{f['featureId']}")
    params = [{"btType": "BTMParameterBoolean-144", "parameterId": p, "value": True} for p in ("buildFeet", "buildPlate")]
    api("POST", f"/partstudios/d/{DID}/w/{WID}/e/{ps}/features", {"feature": {"btType": "BTMFeature-134", "featureType": CRADLE_TYPE, "name": CRADLE_NAME, "namespace": f"e{fsid}::m{mv}", "parameters": params}})
    for _ in range(20):
        feats = api("GET", f"/partstudios/d/{DID}/w/{WID}/e/{ps}/features")
        stt = {f["name"]: feats["featureStates"].get(f["featureId"], {}).get("featureStatus") for f in feats["features"]}
        if all(v in ("OK", "WARNING", "ERROR") for v in stt.values()): break
        time.sleep(4)
    print("  cradle feature:", stt)
    for p in api("GET", f"/parts/d/{DID}/w/{WID}/e/{ps}"): print(f"  cradle part {p['name']}")

def rebuild_cradle_assembly(state):
    """Cradle system: cage tubes + surroundings (car frame) and the cradle parts + cluster scan placed by placement_cradle_T."""
    import numpy as np
    T = np.load(HERE / "output" / "placement_cradle_T.npy")
    old = state.get("cradle_asm")
    if old: api("DELETE", f"/elements/d/{DID}/w/{WID}/e/{old}")
    asm = api("POST", f"/assemblies/d/{DID}/w/{WID}", {"name": "Cradle system (car frame)"})["id"]; state["cradle_asm"] = asm; STATE.write_text(json.dumps(state, indent=1))
    for eid, types in ((state["cage_ps"], ["PARTS"]), (state["surroundings_ps"], ["PARTS"]), (state["surroundings_ps"], ["SURFACES"]), (state["cradle_ps"], ["PARTS"]), (MESH_PS, ["PARTS"]), (MESH_PS, ["SURFACES"])):
        api("POST", f"/assemblies/d/{DID}/w/{WID}/e/{asm}/instances", {"documentId": DID, "elementId": eid, "isWholePartStudio": True, "includePartTypes": types})
    inst = api("GET", f"/assemblies/d/{DID}/w/{WID}/e/{asm}?includeNonSolids=true")["rootAssembly"]["instances"]
    moved = [i["id"] for i in inst if i["elementId"] in (state["cradle_ps"], MESH_PS)]
    M = T.copy(); M[:3, 3] /= 1000.0
    api("POST", f"/assemblies/d/{DID}/w/{WID}/e/{asm}/occurrencetransforms", {"occurrences": [{"path": [i]} for i in moved], "transform": [float(x) for x in M.flatten()], "isRelative": False})
    print(f"cradle assembly rebuilt: {asm} ({len(inst)} instances, {len(moved)} placed by T)")

def rebuild_full_assembly(state):
    """Full system: mount + cage tubes + surroundings in the car frame; enclosure + cluster scan transformed by placement_T."""
    import numpy as np
    T = np.load(HERE / "output" / "placement_T.npy")
    old = state.get("full_asm")
    if old: api("DELETE", f"/elements/d/{DID}/w/{WID}/e/{old}")
    asm = api("POST", f"/assemblies/d/{DID}/w/{WID}", {"name": "Full system (car frame)"})["id"]; state["full_asm"] = asm; STATE.write_text(json.dumps(state, indent=1))
    for eid, types in ((state["mount_ps"], ["PARTS"]), (state["cage_ps"], ["PARTS"]), (state["surroundings_ps"], ["PARTS"]), (state["surroundings_ps"], ["SURFACES"])):
        api("POST", f"/assemblies/d/{DID}/w/{WID}/e/{asm}/instances", {"documentId": DID, "elementId": eid, "isWholePartStudio": True, "includePartTypes": types})
    for eid, types in ((PS, ["PARTS"]), (MESH_PS, ["PARTS"]), (MESH_PS, ["SURFACES"])):
        api("POST", f"/assemblies/d/{DID}/w/{WID}/e/{asm}/instances", {"documentId": DID, "elementId": eid, "isWholePartStudio": True, "includePartTypes": types})
    inst = api("GET", f"/assemblies/d/{DID}/w/{WID}/e/{asm}?includeNonSolids=true")["rootAssembly"]["instances"]
    moved = [i["id"] for i in inst if i["elementId"] in (PS, MESH_PS)]   # every enclosure and cluster-scan body, solids and surfaces
    M = T.copy(); M[:3, 3] /= 1000.0   # Onshape transforms are in metres
    api("POST", f"/assemblies/d/{DID}/w/{WID}/e/{asm}/occurrencetransforms", {"occurrences": [{"path": [i]} for i in moved], "transform": [float(x) for x in M.flatten()], "isRelative": False})
    print(f"full-system assembly rebuilt: {asm} ({len(inst)} instances, {len(moved)} placed by T)")

def upload(path, name):
    """POST a file as a blob element with translation (STEP -> Part Studio). Returns the translation id."""
    global CALLS; CALLS += 1
    auth = (os.environ["ONSHAPE_ACCESS_KEY"], os.environ["ONSHAPE_SECRET_KEY"])
    with open(path, "rb") as f:
        r = requests.post(API + f"/blobelements/d/{DID}/w/{WID}", auth=auth, headers={"Accept": "application/json;charset=UTF-8; qs=0.09"}, timeout=300,
                          files={"file": (name, f, "application/octet-stream")},
                          data={"encodedFilename": name, "translate": "true", "flattenAssemblies": "true", "yAxisIsUp": "false", "allowFaultyParts": "true", "storeInDocument": "true"})
    if r.status_code >= 400: raise SystemExit(f"upload -> {r.status_code}: {r.text[:600]}")
    j = r.json(); print("  upload:", {k: j.get(k) for k in ("id", "name", "translationId", "requestState")})
    return j.get("translationId"), j.get("id")

def push_sidemount(state):
    """sidemount.py writes output/sidemount_car.step (eight parts, car frame, mm). Replace the Part Studio made from it."""
    for key in ("sidemount_ps", "sidemount_blob"):      # the translated Part Studio and the uploaded STEP tab
        old = state.pop(key, None)
        if old: api("DELETE", f"/elements/d/{DID}/w/{WID}/e/{old}"); STATE.write_text(json.dumps(state, indent=1))
    tid, blob_id = upload(HERE / "output" / "sidemount_car.step", "sidemount_car.step")
    state["sidemount_blob"] = blob_id; STATE.write_text(json.dumps(state, indent=1))
    tr = {}
    for _ in range(40):
        tr = api("GET", f"/translations/{tid}")
        if tr.get("requestState") in ("DONE", "FAILED"): break
        time.sleep(5)
    if tr.get("requestState") != "DONE": raise SystemExit("translation did not finish: " + json.dumps(tr)[:800])
    ids = tr.get("resultElementIds") or []
    if not ids: raise SystemExit("translation returned no element: " + json.dumps(tr)[:800])
    ps = ids[0]; state["sidemount_ps"] = ps; STATE.write_text(json.dumps(state, indent=1)); print("side mount Part Studio", ps, "(all result elements:", ids, ")")
    bb = api("GET", f"/partstudios/d/{DID}/w/{WID}/e/{ps}/boundingboxes")
    print("  bounding box (m):", {k: round(v, 3) for k, v in bb.items() if isinstance(v, (int, float))})   # expect ~0.33 x 0.17 x 0.17 m; metres-as-mm would be 1000x

def rebuild_sidemount_assembly(state):
    """Side mount system: cage tubes + surroundings + mount parts (already in the car frame) + the cluster scan placed by placement_sidemount_T."""
    import numpy as np
    T = np.load(HERE / "output" / "placement_sidemount_T.npy")
    old = state.get("sidemount_asm")
    if old: api("DELETE", f"/elements/d/{DID}/w/{WID}/e/{old}")
    asm = api("POST", f"/assemblies/d/{DID}/w/{WID}", {"name": "Side mount system (car frame)"})["id"]; state["sidemount_asm"] = asm; STATE.write_text(json.dumps(state, indent=1))
    for eid, types in ((state["cage_ps"], ["PARTS"]), (state["surroundings_ps"], ["PARTS"]), (state["surroundings_ps"], ["SURFACES"]), (state["sidemount_ps"], ["PARTS"]), (MESH_PS, ["PARTS"]), (MESH_PS, ["SURFACES"])):
        api("POST", f"/assemblies/d/{DID}/w/{WID}/e/{asm}/instances", {"documentId": DID, "elementId": eid, "isWholePartStudio": True, "includePartTypes": types})
    inst = api("GET", f"/assemblies/d/{DID}/w/{WID}/e/{asm}?includeNonSolids=true")["rootAssembly"]["instances"]
    moved = [i["id"] for i in inst if i["elementId"] == MESH_PS]
    M = T.copy(); M[:3, 3] /= 1000.0
    api("POST", f"/assemblies/d/{DID}/w/{WID}/e/{asm}/occurrencetransforms", {"occurrences": [{"path": [i]} for i in moved], "transform": [float(x) for x in M.flatten()], "isRelative": False})
    print(f"side mount assembly rebuilt: {asm} ({len(inst)} instances, {len(moved)} cluster bodies placed by T)")
    print(f"open: https://cad.onshape.com/documents/{DID}/w/{WID}/e/{asm}")

if __name__ == "__main__":
    main()
