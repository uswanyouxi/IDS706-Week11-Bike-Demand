"""Fetch unmodified classroom references into ignored artifacts/, verify Git blobs."""
import hashlib,json,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def fetch():
    manifest=json.loads((ROOT/"bonus/classroom_sources.json").read_text())
    target=ROOT/"artifacts/classroom-reference"
    for name,digest in manifest["git_blob_sha1"].items():
        path=target/name
        if path.exists():
            data=path.read_bytes()
        else:
            url=f"https://raw.githubusercontent.com/{manifest['repository']}/{manifest['commit']}/{name}"
            with urllib.request.urlopen(url,timeout=45) as response:data=response.read()
            actual=hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
            if actual!=digest:raise ValueError("Reference checksum mismatch: "+name)
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        assert hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()==digest,name
    print(json.dumps({"commit":manifest["commit"],"files":len(manifest["git_blob_sha1"]),
        "cache":"artifacts/classroom-reference","unmodified":True}))
if __name__=="__main__":fetch()
