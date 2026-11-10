"""Lightweight guards: no Docker startup, network calls, database writes or fits."""
import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from isolation import PROJECT,CAPS,validate_config
ROOT=Path(__file__).resolve().parents[2]
def fixture():
    services={}
    for name,(ram,cpu) in CAPS.items():
        services[name]={"mem_limit":ram*1024**2,"cpus":cpu,"restart":"no","environment":{},"volumes":[]}
    services["native-loop-worker"]["network_mode"]="none"
    services["native-loop-worker"]["environment"]={"OPENROUTER_API_KEY":"","CURSOR_API_KEY":""}
    for name,published,target in [("native-webserver",8088,8080),("native-viewer",8503,8503)]:
        services[name]["ports"]=[{"host_ip":"127.0.0.1","published":published,"target":target}]
    return {"name":PROJECT,"services":services,"networks":{"default":{"name":PROJECT+"_default"}},
        "volumes":{n:{"name":PROJECT+"_"+n} for n in ["native-metadata","native-repository","native-logs","native-evidence"]}}
class IsolationTests(unittest.TestCase):
    def setUp(self):self.config=fixture()
    def rejected(self):self.assertRaises(AssertionError,validate_config,self.config,ROOT)
    def test_valid_native_project(self):self.assertTrue(validate_config(self.config,ROOT))
    def test_no_external_volume_alias(self):
        self.config["volumes"]["native-repository"]["name"]="ids706-bike-demand_project-artifacts";self.rejected()
    def test_no_external_network(self):
        self.config["networks"]["default"]["external"]=True;self.rejected()
    def test_no_existing_network_name(self):
        self.config["networks"]["default"]["name"]="ids706-bike-demand_default";self.rejected()
    def test_no_production_credentials(self):
        self.config["services"]["native-loop-worker"]["environment"]["APP_DB_PASSWORD"]="sentinel";self.rejected()
    def test_no_project_root_or_env_mount(self):
        self.config["services"]["native-loop-worker"]["volumes"]=[{"type":"bind","source":str(ROOT),"read_only":True}];self.rejected()
    def test_no_writable_reference_bind(self):
        self.config["services"]["native-scheduler"]["volumes"]=[{"type":"bind","source":str(ROOT/"artifacts/native-classroom-reference"),"read_only":False}];self.rejected()
    def test_no_public_ui_binding(self):
        self.config["services"]["native-webserver"]["ports"][0]["host_ip"]="0.0.0.0";self.rejected()
    def test_no_existing_ui_port(self):
        self.config["services"]["native-webserver"]["ports"][0]["published"]=8080;self.rejected()
    def test_no_memory_cap_expansion(self):
        self.config["services"]["native-loop-worker"]["mem_limit"]=2*1024**3;self.rejected()
    def test_no_paid_api(self):
        self.config["services"]["native-loop-worker"]["environment"]["OPENROUTER_API_KEY"]="sentinel";self.rejected()
    def test_native_worker_cannot_make_external_api_calls(self):
        self.config["services"]["native-loop-worker"]["network_mode"]="bridge";self.rejected()
    def test_absent_runtime_evidence_cannot_pass(self):
        import tempfile
        from verify_native import verify_native
        with tempfile.TemporaryDirectory() as folder:
            self.assertRaises(FileNotFoundError,verify_native,folder)
    def test_memory_gate_prevents_any_container_start(self):
        from unittest.mock import patch
        import control
        with patch.object(control,"resources",side_effect=AssertionError("memory gate")), patch.object(control,"runlog") as run:
            self.assertRaises(AssertionError,control.start)
            run.assert_not_called()
    def test_retry_logging_preserves_original_bytes_and_timestamp(self):
        import tempfile
        from unittest.mock import patch
        import control
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder);old=out/"probe.log";old.write_bytes(b"genuine original output\n")
            before=old.stat().st_mtime_ns
            with patch.object(control,"OUT",out):control.runlog("probe",[sys.executable,"-c","print('new observation')"])
            self.assertEqual(old.read_bytes(),b"genuine original output\n")
            self.assertEqual(old.stat().st_mtime_ns,before)
            self.assertIn("new observation",(out/"probe-attempt2.log").read_text())
    def test_no_unplanned_service(self):
        self.config["services"]["gateway"]={};self.rejected()
if __name__=="__main__":unittest.main(verbosity=2)
