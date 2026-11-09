"""Graph visuals derived from compiled nodes/edges and recorded runtime events."""
import json

def graph_dot(graph,events):
    completed={e["node"] for e in events if e["kind"]=="node_completed"}
    active=events[-1]["node"] if events and events[-1]["kind"]=="node_started" else None
    failed=events[-1].get("error") if events else None
    traversed={(e.get("from_node"),e["node"]) for e in events if e["kind"]=="node_started"}
    def quote(value):return json.dumps(str(value))
    lines=["digraph ML { rankdir=LR; node [shape=box, style=\"rounded,filled\", fontname=\"Arial\"];"]
    for item in graph["nodes"]:
        name=str(item["id"])
        color="#b9e6c9" if name in completed else "#e5eaf0"
        if name==active:color="#ffd787" if not failed else "#f6b3b3"
        label=name.replace("_","\n")
        lines.append(f"{quote(name)} [label={quote(label)},fillcolor={quote(color)}];")
    for edge in graph["edges"]:
        a,b=str(edge["source"]),str(edge["target"])
        color="#007f86" if (a,b) in traversed else "#9aa5b1"
        style="dashed" if edge.get("conditional") else "solid"
        label=edge.get("data") or ""
        lines.append(f"{quote(a)} -> {quote(b)} [color={quote(color)},style={quote(style)},label={quote(label)}];")
    lines.append("}")
    return "\n".join(lines)

def save_graph_png(graph,events,path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch
    # Layout only; every node and edge comes from the actual compiled graph.
    positions={"__start__":(0,1),"load_postgres":(1,1),"prepare_features":(2,1),
        "dummy_baseline":(3,1),"choose_candidate":(4,1),"train_model":(5,1),
        "evaluate_validation":(6,1),"conditional_router":(7,1),"final_test_once":(8,1),
        "report":(9,1),"__end__":(10,1),"failure_report":(5,-1)}
    names=[str(n["id"]) for n in graph["nodes"]]
    for name in names:assert name in positions
    visited={e["node"] for e in events if e["kind"]=="node_completed"}
    actual={(e.get("from_node"),e["node"]) for e in events if e["kind"]=="node_started"}
    fig,ax=plt.subplots(figsize=(18,6))
    for edge in graph["edges"]:
        a,b=str(edge["source"]),str(edge["target"])
        start,end=positions[a],positions[b]
        curve=0.35 if a=="conditional_router" and b=="choose_candidate" else (0.10 if b=="failure_report" else 0)
        patch=FancyArrowPatch(start,end,arrowstyle="-|>",mutation_scale=12,
            connectionstyle=f"arc3,rad={curve}",shrinkA=30,shrinkB=30,
            linewidth=1.8 if (a,b) in actual else 0.7,color="#007f86" if (a,b) in actual else "#b5bec8",
            linestyle="--" if edge.get("conditional") else "-")
        ax.add_patch(patch)
    for name in names:
        x,y=positions[name]
        visits=sum(e["node"]==name and e["kind"]=="node_completed" for e in events)
        label=name.replace("_","\n")+f"\nvisits: {visits}"
        ax.text(x,y,label,ha="center",va="center",fontsize=8,
            bbox=dict(boxstyle="round,pad=0.35",facecolor="#c7ead9" if name in visited else "#e7ebf0",edgecolor="#496170"))
    ax.set(xlim=(-0.5,10.5),ylim=(-1.8,2.5),title="Original compiled LangGraph — actual execution visits (artifact, not UI screenshot)")
    ax.axis("off");fig.tight_layout();fig.savefig(path,dpi=150);plt.close(fig)
