# -*- coding: utf-8 -*-
"""P7-C：Branch A 认知沙盒执行验证（REWRITTEN）。

P7 副本 branch_a_copy/ 仅添加 __init__.py（包结构），模块源码与 extracted 字节一致
（sha256 逐文件比对并写入 BRANCH_A_RESULTS.csv 的 provenance 区）。
可执行子集：cmawse.core.schema + cmawse.world.bus（PrivateHorizon / PublicRealityBus）。
断裂面（不得以子集结果外推）：agent.cognitive_state / deliberation / representation 模块
在提取树中不存在（全仓 grep 无类定义）；agent.llm_boundary 仅存于 quarantine 且 compile=FAIL。
"""
import sys, os, csv, shutil, hashlib, importlib.util, json
ROOT = '/Users/liyang/Documents/CMAWSE-REBUILD'
SRC = os.path.join(ROOT, 'extracted', 'src')
COPY = os.path.join(ROOT, 'rebuild', 'p7', 'branch_a_copy')

def build_copy():
    if os.path.exists(COPY):
        shutil.rmtree(COPY)
    os.makedirs(COPY)
    # 仅复制 bus + schema + 其依赖链（自洽子集）
    pkgs = ['cmawse', 'cmawse/core', 'cmawse/world']
    mods = ['cmawse/core/schema.py', 'cmawse/world/bus.py']
    for pkg in pkgs:
        os.makedirs(os.path.join(COPY, pkg), exist_ok=True)
        open(os.path.join(COPY, pkg, '__init__.py'), 'w').write('# REWRITTEN-P7: package shim (extracted 树无 __init__.py)' + chr(10))
    prov = []
    for m in mods:
        s = open(os.path.join(SRC, m), 'rb').read()
        open(os.path.join(COPY, m), 'wb').write(s)
        h = hashlib.sha256(s).hexdigest()
        prov.append((m, h))
    return prov

def load_bus():
    spec = importlib.util.spec_from_file_location('cmawse.world.bus', os.path.join(COPY, 'cmawse', 'world', 'bus.py'))
    import cmawse.core.schema as S  # 副本包内（COPY 在 sys.path 首位）
    mod = importlib.util.module_from_spec(spec)
    sys.modules['cmawse.world.bus'] = mod
    spec.loader.exec_module(mod)
    return mod, S

def main():
    prov = build_copy()
    sys.path.insert(0, COPY)
    bus, S = load_bus()
    rows, log = [], ['== P7-C Branch A 执行验证 ==', '副本 sha256 与 extracted 一致：' + ('ALL' if all(open(os.path.join(SRC, m), 'rb').read() == open(os.path.join(COPY, m), 'rb').read() for m, _ in prov) else 'MISMATCH') + f' ({[m for m, _ in prov]})', '']
    for m, h in prov:
        rows.append({'case': 'PROVENANCE', 'detail': m, 'expected': 'byte-identical', 'observed': h[:16] + '...', 'verdict': 'MATCH' if open(os.path.join(SRC, m), 'rb').read() == open(os.path.join(COPY, m), 'rb').read() else 'DIFF'})

    def V3(x=0.0, y=0.0, z=0.0):
        return S.Vector3D(x=x, y=y, z=z)

    def somatic(deprived=False):
        return S.SomaticState(energy_pool=1.0, integrity=1.0, load=0.0, sensory_deprived=deprived, variables={})

    def actor(pos, deprived=False):
        soc = S.SocialState() if hasattr(S, 'SocialState') else None
        narr = S.SelfNarrativeState() if hasattr(S, 'SelfNarrativeState') else None
        return S.ActorSnapshot(position=pos, somatic=somatic(deprived), social=soc,
                               self_narrative=narr, bound_objects={})

    def env():
        return S.PhysicalEnvironmentSnapshot(temperature=20.0, observation_pressure=1.0,
                                             friction_coefficient=0.5, micro_entropy_variable=0.0, properties={})

    def gw(actors, tick=0):
        return S.GlobalWorldState(tick=tick, timestamp='t0', actors=actors, environment=env(), objects={})

    A = actor(V3(0, 0, 0))
    B = actor(V3(100, 0, 0))       # 远超 15 视距
    Cn = actor(V3(10, 0, 0))       # 视距内
    Ddep = actor(V3(0, 0, 0), deprived=True)  # 感官剥夺，且在发声者旁

    # 案例 1：视距外隔离
    hz = bus.PublicRealityBus().generate_horizons(gw({'a': A, 'b': B}))['a']
    v1 = 'b' not in hz.visible_actors
    rows.append({'case': 'C1_out_of_range_not_visible', 'detail': 'dist=100 > limit=15', 'expected': 'b 不在 a 的 visible_actors', 'observed': str(dict(hz.visible_actors)), 'verdict': 'PASS' if v1 else 'FAIL'})
    # 案例 2：视距内可见
    hz2 = bus.PublicRealityBus().generate_horizons(gw({'a': A, 'c': Cn}))['a']
    v2 = 'c' in hz2.visible_actors
    rows.append({'case': 'C2_in_range_visible', 'detail': 'dist=10 <= 15', 'expected': 'c 可见', 'observed': str(dict(hz2.visible_actors)), 'verdict': 'PASS' if v2 else 'FAIL'})
    # 案例 3a：horizon 属性赋值被 frozen 拒绝
    try:
        hz.tick = 5
        v3a = False; obs3a = 'attr assignment accepted'
    except Exception as e:
        v3a = True; obs3a = type(e).__name__
    rows.append({'case': 'C3a_horizon_attr_frozen', 'detail': 'hz.tick = 5', 'expected': '拒绝', 'observed': obs3a, 'verdict': 'PASS' if v3a else 'FAIL'})
    # 案例 3b：容器内容变异（真实发现：frozen 不保护 dict 内容）
    try:
        hz.visible_actors['b'] = V3(1, 1, 1)
        v3b = False; obs3b = 'in-place dict mutation ACCEPTED（机制缺口）'
    except Exception as e:
        v3b = True; obs3b = type(e).__name__
    rows.append({'case': 'C3b_horizon_dict_mutation', 'detail': "hz.visible_actors['b'] = pos", 'expected': '拒绝（理想）', 'observed': obs3b, 'verdict': 'PASS' if v3b else 'FAIL'})
    # 案例 4：声学衰减隔离（60dB：100m 收 0dB 不可闻；2m 收 60-20*sqrt(2)≈31.8dB 可闻）
    hzA = bus.PublicRealityBus().generate_horizons(gw({'a': A, 'b': B}), previous_tick_emissions=[{'speaker_id': 'b', 'content': 'secret', 'intensity_db': 60.0}])['a']
    Bn = actor(V3(2, 0, 0))
    hzC = bus.PublicRealityBus().generate_horizons(gw({'a': A, 'c': Bn}), previous_tick_emissions=[{'speaker_id': 'c', 'content': 'hello', 'intensity_db': 60.0}])['a']
    v4 = (len(hzA.audible_emissions) == 0) and (len(hzC.audible_emissions) == 1)
    rows.append({'case': 'C4_acoustic_attenuation', 'detail': '60dB@100m vs 60dB@2m', 'expected': '远者不可闻/近者可闻', 'observed': f'far={len(hzA.audible_emissions)}, near={len(hzC.audible_emissions)}', 'verdict': 'PASS' if v4 else 'FAIL'})
    # 案例 5：感官剥夺者空视界（即使 1m 内有他人发声）
    hzD = bus.PublicRealityBus().generate_horizons(gw({'d': Ddep, 'c': Cn}), previous_tick_emissions=[{'speaker_id': 'c', 'content': 'loud', 'intensity_db': 90.0}])['d']
    v5 = (len(hzD.visible_actors) == 0) and (len(hzD.audible_emissions) == 0)
    rows.append({'case': 'C5_sensory_deprived_empty', 'detail': '剥夺者 10m 内 90dB 发声', 'expected': '无感知', 'observed': f'vis={len(hzD.visible_actors)}, aud={len(hzD.audible_emissions)}', 'verdict': 'PASS' if v5 else 'FAIL'})
    # 案例 6：确定性重放
    g = gw({'a': A, 'b': B, 'c': Cn})
    em = [{'speaker_id': 'c', 'content': 'x', 'intensity_db': 60.0}]
    r1 = bus.PublicRealityBus().generate_horizons(g, em)
    r2 = bus.PublicRealityBus().generate_horizons(g, em)
    v6 = all(r1[k].model_dump() == r2[k].model_dump() for k in r1)
    rows.append({'case': 'C6_deterministic_replay', 'detail': 'generate_horizons 两次', 'expected': '逐主体相等', 'observed': 'equal' if v6 else 'DIFFER', 'verdict': 'PASS' if v6 else 'FAIL'})
    # 案例 7：目击资格按视界过滤
    ev = S.VerifiedEventEntry(event_id='e1', tick_index=0, timestamp='t0', causal_status='CONFIRMED',
                               resolved_kinematics=[{'agent_id': 'a', 'target_id': 'c'}], acoustic_emissions=[], state_patches=[])
    if ev is not None:
        hz_all = bus.PublicRealityBus().generate_horizons(g, em)
        wit = bus.PublicRealityBus().filter_witnesses(ev, g, hz_all)
        # 参与者 a/c 合格；b（视距外、非参与、不可闻）应不合格
        v7 = ('a' in wit) and ('c' in wit) and ('b' not in wit)
        rows.append({'case': 'C7_witness_qualification', 'detail': '直接参与合格 / 视听外非参与者不合格', 'expected': "a,c in; b out", 'observed': str(wit), 'verdict': 'PASS' if v7 else 'FAIL'})

    for r in rows:
        if r['case'] != 'PROVENANCE':
            log.append(f"  {r['case']:28s} {r['verdict']:5s} obs={r['observed'][:60]}")
    n_pass = sum(1 for r in rows if r['verdict'] == 'PASS')
    cases = sum(1 for r in rows if r['case'] != 'PROVENANCE')
    log.append('')
    log.append(f'可执行子集案例：{n_pass}/{cases} PASS')
    log.append('不可执行断裂面：agent.cognitive_state / agent.deliberation / agent.representation 不在提取树；agent.llm_boundary 仅 quarantine compile=FAIL；测试层需 pytest（已装）但 import 链断于上述缺失模块。')
    csvp = os.path.join(ROOT, 'rebuild', 'p7', 'BRANCH_A_RESULTS.csv')
    with open(csvp, 'w', newline='', encoding='utf-8') as f:
        wr = csv.DictWriter(f, fieldnames=['case', 'detail', 'expected', 'observed', 'verdict']); wr.writeheader(); wr.writerows(rows)
    log.append(f'CSV: {csvp} rows={len(rows)}')
    open(os.path.join(ROOT, 'rebuild', 'p7', 'logs', 'C_branch_a.log'), 'w', encoding='utf-8').write(chr(10).join(log))
    print(chr(10).join(log))

if __name__ == '__main__':
    main()
