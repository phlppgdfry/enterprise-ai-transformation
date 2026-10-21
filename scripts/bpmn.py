"""BPMN 2.0 files (with diagram layout) for the doc desk process, as-is and to-be.

Small generator instead of hand-drawn XML: lanes, a column per step, flows
routed with right angles. Opens in Camunda Modeler, bpmn.io and Signavio.
"""

from xml.sax.saxutils import quoteattr

LANE_H, COL_W, X0, POOL_LABEL = 130, 170, 60, 30
SIZES = {"start": (36, 36), "end": (36, 36), "task": (130, 70), "gateway": (50, 50)}
TAGS = {"start": "startEvent", "end": "endEvent", "task": "task", "gateway": "exclusiveGateway"}


def process(pid, name, lanes, nodes, flows):
    """lanes: [(id, name)]; nodes: [(id, kind, name, lane, col)]; flows: [(src, dst, label)]."""
    lane_y = {lid: i * LANE_H for i, (lid, _) in enumerate(lanes)}
    box = {}
    for nid, kind, _, lane, col in nodes:
        w, h = SIZES[kind]
        cx = X0 + POOL_LABEL + col * COL_W + COL_W / 2
        cy = lane_y[lane] + LANE_H / 2
        box[nid] = (cx - w / 2, cy - h / 2, w, h)
    width = X0 + POOL_LABEL + (max(n[4] for n in nodes) + 1) * COL_W + 40
    height = len(lanes) * LANE_H

    sem = [f'<bpmn:process id="{pid}" name={quoteattr(name)} isExecutable="false">',
           f'<bpmn:laneSet id="{pid}_lanes">']
    for lid, lname in lanes:
        refs = "".join(f"<bpmn:flowNodeRef>{n[0]}</bpmn:flowNodeRef>" for n in nodes if n[3] == lid)
        sem.append(f'<bpmn:lane id="{lid}" name={quoteattr(lname)}>{refs}</bpmn:lane>')
    sem.append("</bpmn:laneSet>")
    incoming = {n[0]: [] for n in nodes}
    outgoing = {n[0]: [] for n in nodes}
    for i, (s, d, _) in enumerate(flows):
        outgoing[s].append(f"{pid}_f{i}")
        incoming[d].append(f"{pid}_f{i}")
    for nid, kind, nname, _, _ in nodes:
        inner = "".join(f"<bpmn:incoming>{f}</bpmn:incoming>" for f in incoming[nid])
        inner += "".join(f"<bpmn:outgoing>{f}</bpmn:outgoing>" for f in outgoing[nid])
        sem.append(f'<bpmn:{TAGS[kind]} id="{nid}" name={quoteattr(nname)}>{inner}</bpmn:{TAGS[kind]}>')
    for i, (s, d, label) in enumerate(flows):
        lab = f" name={quoteattr(label)}" if label else ""
        sem.append(f'<bpmn:sequenceFlow id="{pid}_f{i}" sourceRef="{s}" targetRef="{d}"{lab}/>')
    sem.append("</bpmn:process>")

    node_at = {n[0]: (n[3], n[4]) for n in nodes}
    di = [f'<bpmndi:BPMNShape id="{pid}_pool_di" bpmnElement="{pid}_pool" isHorizontal="true">'
          f'<dc:Bounds x="{X0}" y="0" width="{width - X0}" height="{height}"/></bpmndi:BPMNShape>']
    for lid, _ in lanes:
        di.append(f'<bpmndi:BPMNShape id="{lid}_di" bpmnElement="{lid}" isHorizontal="true">'
                  f'<dc:Bounds x="{X0 + POOL_LABEL}" y="{lane_y[lid]}" width="{width - X0 - POOL_LABEL}" height="{LANE_H}"/></bpmndi:BPMNShape>')
    for nid, kind, _, _, _ in nodes:
        x, y, w, h = box[nid]
        marker = ' isMarkerVisible="true"' if kind == "gateway" else ""
        di.append(f'<bpmndi:BPMNShape id="{nid}_di" bpmnElement="{nid}"{marker}>'
                  f'<dc:Bounds x="{x:.0f}" y="{y:.0f}" width="{w}" height="{h}"/></bpmndi:BPMNShape>')
    for i, (s, d, _) in enumerate(flows):
        sx, sy, sw, sh = box[s]
        dx, dy, dw, dh = box[d]
        lane_s, col_s = node_at[s]
        lane_d, col_d = node_at[d]
        blocked = lane_s == lane_d and any(
            n[3] == lane_s and col_s < n[4] < col_d for n in nodes)
        if col_s == col_d:  # same column, other lane: straight up or down
            down = dy > sy
            a = (sx + sw / 2, sy + sh if down else sy)
            b = (dx + dw / 2, dy if down else dy + dh)
            pts = [a, b]
        elif dx > sx and blocked:  # same lane, something in between: go round underneath
            bottom = lane_y[lane_s] + LANE_H - 14
            a, b = (sx + sw / 2, sy + sh), (dx + dw / 2, dy + dh)
            pts = [a, (a[0], bottom), (b[0], bottom), b]
        elif dx > sx:
            a, b = (sx + sw, sy + sh / 2), (dx, dy + dh / 2)
            turn = dx - 20
            pts = [a, b] if abs(a[1] - b[1]) < 1 else [a, (turn, a[1]), (turn, b[1]), b]
        else:  # loop back: leave from the top, come in from the top
            a, b = (sx + sw / 2, sy), (dx + dw / 2, dy)
            top = min(sy, dy) - 22
            pts = [a, (a[0], top), (b[0], top), b]
        wps = "".join(f'<di:waypoint x="{x:.0f}" y="{y:.0f}"/>' for x, y in pts)
        di.append(f'<bpmndi:BPMNEdge id="{pid}_f{i}_di" bpmnElement="{pid}_f{i}">{wps}</bpmndi:BPMNEdge>')
    return "".join(sem), "".join(di), width


def document(pid, name, lanes, nodes, flows):
    sem, di, _ = process(pid, name, lanes, nodes, flows)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
            'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" '
            'xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" '
            'xmlns:di="http://www.omg.org/spec/DD/20100524/DI" '
            f'id="{pid}_defs" targetNamespace="https://wendelkaai.example/bpmn">\n'
            f'<bpmn:collaboration id="{pid}_collab"><bpmn:participant id="{pid}_pool" '
            f'name={quoteattr(name)} processRef="{pid}"/></bpmn:collaboration>\n'
            + sem + "\n"
            f'<bpmndi:BPMNDiagram id="{pid}_diagram"><bpmndi:BPMNPlane id="{pid}_plane" bpmnElement="{pid}_collab">'
            + di + "</bpmndi:BPMNPlane></bpmndi:BPMNDiagram>\n</bpmn:definitions>\n")


def as_is():
    lanes = [("L_ship", "Shipper / agent"), ("L_desk", "Doc desk clerk"), ("L_ops", "Operations and customs")]
    nodes = [
        ("s1", "start", "Document e-mail received", "L_desk", 0),
        ("t1", "task", "Find the shipment and the document type", "L_desk", 1),
        ("g1", "gateway", "Set complete?", "L_desk", 2),
        ("t2", "task", "Chase missing documents", "L_desk", 3),
        ("t3", "task", "Send missing document", "L_ship", 3),
        ("t4", "task", "Key all fields into the TMS", "L_desk", 4),
        ("t5", "task", "Compare with booking and other documents", "L_desk", 5),
        ("g2", "gateway", "Discrepancy?", "L_desk", 6),
        ("t6", "task", "Ask for a corrected document", "L_ship", 7),
        ("t7", "task", "Plan transport and prepare customs declaration", "L_ops", 7),
        ("e1", "end", "Shipment ready", "L_ops", 8),
    ]
    flows = [("s1", "t1", ""), ("t1", "g1", ""), ("g1", "t4", "yes"), ("g1", "t2", "no"),
             ("t2", "t3", ""), ("t3", "t1", ""), ("t4", "t5", ""), ("t5", "g2", ""),
             ("g2", "t6", "yes"), ("t6", "t4", ""), ("g2", "t7", "no"), ("t7", "e1", "")]
    return document("AsIs", "Doc desk: inbound freight documents (as-is)", lanes, nodes, flows)


def to_be():
    lanes = [("L_sys", "Document pipeline"), ("L_desk", "Doc desk clerk"), ("L_ops", "Operations and customs")]
    nodes = [
        ("s1", "start", "Document e-mail received", "L_sys", 0),
        ("t1", "task", "Classify and extract fields", "L_sys", 1),
        ("t2", "task", "Validate (V01-V14) incl. cross-document checks", "L_sys", 2),
        ("g1", "gateway", "Route", "L_sys", 3),
        ("t3", "task", "Post record to the TMS", "L_sys", 5),
        ("t4", "task", "Check only the flagged fields, confirm or correct", "L_desk", 4),
        ("t5", "task", "Handle by hand (not a freight document or type unsure)", "L_desk", 5),
        ("t6", "task", "5% random audit of straight-through documents", "L_desk", 6),
        ("t7", "task", "Plan transport and prepare customs declaration", "L_ops", 6),
        ("e1", "end", "Shipment ready", "L_ops", 7),
        ("e2", "end", "Audit result logged", "L_desk", 7),
    ]
    flows = [("s1", "t1", ""), ("t1", "t2", ""), ("t2", "g1", ""), ("g1", "t3", "auto"),
             ("g1", "t4", "review"), ("g1", "t5", "manual"), ("t4", "t3", ""),
             ("t3", "t6", ""), ("t3", "t7", ""), ("t5", "t7", ""), ("t6", "e2", ""), ("t7", "e1", "")]
    return document("ToBe", "Doc desk: inbound freight documents (to-be, with the pilot)", lanes, nodes, flows)
