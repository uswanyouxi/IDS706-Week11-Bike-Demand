"""Native metadata/user initialization. Never connects to the existing project."""
import json,os,subprocess
def cli(*args):
    r=subprocess.run(["airflow",*args],capture_output=True,text=True)
    output=(r.stdout+r.stderr).replace(os.environ["NATIVE_ADMIN_PASSWORD"],"[REDACTED]")
    print(output,end="")
    if r.returncode:raise RuntimeError("Native initialization command failed")
    return r.stdout
cli("db","migrate")
cli("db","check")
users=cli("users","list","--output","json")
records=json.loads(users[users.find("[{"):] if "[{" in users else users[users.rfind("[]"):])
existing=[u for u in records if u.get("username")=="native_admin"]
if existing:
    assert "Admin" in str(existing[0].get("roles")),"Existing native user is not an administrator"
else:
    cli("users","create","--username","native_admin","--firstname","Native","--lastname","Classroom",
        "--role","Admin","--email","native-admin@example.invalid","--password",os.environ["NATIVE_ADMIN_PASSWORD"])
print("Native metadata and administrator initialized; credentials are not printed.")
