"""Pure isolation checks, separate from all existing production/evaluation code."""
from pathlib import Path
PROJECT="ids706-classroom-native-v1"
CAPS={"native-storage-init":(128,0.25),"native-airflow-init":(768,1),"native-db":(256,0.5),
      "native-scheduler":(1024,1),"native-webserver":(768,0.5),"native-loop-worker":(768,1),"native-viewer":(256,0.5)}
def validate_config(cfg,root):
    root=Path(root).resolve()
    assert cfg["name"]==PROJECT
    assert set(cfg["services"])==set(CAPS)
    assert set(cfg["volumes"])=={"native-metadata","native-repository","native-logs","native-evidence"}
    for item in [*cfg["volumes"].values(),*cfg["networks"].values()]:
        assert not item.get("external")
        assert item["name"].startswith(PROJECT+"_")
    allowed=[root/p for p in ["bonus/native-classroom","artifacts/native-classroom-reference",
        "docs/verification/bonus/runtime/evaluations/bonus_suite_01","src","tests","scripts","sql","requirements","dags","data/raw","pytest.ini"]]
    for name,s in cfg["services"].items():
        assert s.get("restart","no")=="no"
        assert int(s["mem_limit"])<=CAPS[name][0]*1024**2 and float(s["cpus"])<=CAPS[name][1]
        assert not any(k.startswith("APP_DB") for k in s.get("environment",{}))
        ports=s.get("ports",[])
        expected={"native-webserver":(8088,8080),"native-viewer":(8503,8503)}.get(name)
        assert len(ports)==int(expected is not None)
        for port in ports:
            assert port["host_ip"]=="127.0.0.1"
            assert (int(port["published"]),int(port["target"]))==expected
        for mount in s.get("volumes",[]):
            if mount["type"]=="volume":assert mount["source"] in cfg["volumes"]
            elif mount["type"]=="bind":
                assert mount.get("read_only") is True
                source=Path(mount["source"]).resolve()
                assert any(source==p or p in source.parents for p in allowed),str(source)
            else:raise AssertionError("Unexpected mount type")
    assert cfg["services"]["native-loop-worker"].get("network_mode")=="none"
    assert cfg["services"]["native-loop-worker"]["environment"].get("OPENROUTER_API_KEY")==""
    assert cfg["services"]["native-loop-worker"]["environment"].get("CURSOR_API_KEY")==""
    return True
