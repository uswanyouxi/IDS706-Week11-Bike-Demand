"""AppTest reads the actual native reports; no fitting or database access."""
import json
from pathlib import Path
from streamlit.testing.v1 import AppTest
ROOT=Path("/evidence/native_classroom_01")
app=AppTest.from_file("/harness/viewer.py").run(timeout=60)
assert not app.exception,list(app.exception)
values=[m.value for m in app.metric]
for expected in ["0.050000","1600","400","3","0.056604","0.059113","0.522500"]:
    assert expected in values,(expected,values)
assert len(app.get("graphviz_chart"))==1
assert len(app.dataframe)>=5
result={"backend_app_test":"passed","real_report_metrics_visible":values,"dataframe_count":len(app.dataframe),
        "compiled_graph_visible":True,"exceptions":[],"screenshots_captured":False}
with (ROOT/"viewer-apptest.json").open("x",encoding="utf-8") as f:json.dump(result,f,indent=2);f.write("\n")
print(json.dumps(result,indent=2))
