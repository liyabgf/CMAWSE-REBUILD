# -*- coding: utf-8 -*-
"""P8 独立程序最小可行性验证（REWRITTEN）：官方 deepseek-harness-sdk 从独立 Python 进程调用模型。

不读取/不复制凭据值：仅把 dsh_home 指向用户已有 Harness home（官方 SDK 显式参数），
凭据解析由 SDK/profile 内部完成。请求/响应/路由/时间/异常全量落盘。
"""
import json, time, sys, os, hashlib

PROMPT_FILE = '/Users/liyang/Documents/CMAWSE-REBUILD/rebuild/p8/llm_integration/smoke_payload.json'
OUT = '/Users/liyang/Documents/CMAWSE-REBUILD/rebuild/p8/llm_integration/raw/sdk_call_result.json'

def build_subject_prompt():
    p = json.load(open(PROMPT_FILE))
    lines = ['你是 CMAWSE 仿真中的主体（subject）。根据历史事件学习世界转移规律，为每条查询预测 next_state。',
             '历史（object, action -> next_state）：']
    for s in p['context_history']:
        lines.append(f"  {s['object']} + {s['action']} -> {s['next_state']}")
    lines.append('查询（tau, X, act）：')
    for q in p['d1_queries']:
        lines.append(f"  tau={q['tau']}: {q['X']} + {q['act']}")
    lines.append('只输出一个 JSON 对象，格式：')
    lines.append('{"d1_predictions": {"<tau字符串>": "q0|q1|q2", ...共9条}, "d2_matrix": {"M1": {"<action>": "q0|q1|q2"}}, "d4_predictions": {"k": "q0"}, "d5_prediction": "q0"}')
    lines.append('不要任何其他文字或代码围栏。')
    return chr(10).join(lines)

def main():
    record = {'started_at': time.time(), 'dsh_home_source': '~/.dsh (用户已有 home，官方 SDK 显式参数；凭据值未读取未复制)',
              'sdk': 'deepseek-harness-sdk (pip)', 'prompt_sha256': None, 'route': None}
    prompt = build_subject_prompt()
    record['prompt_sha256'] = hashlib.sha256(prompt.encode()).hexdigest()
    from deepseek_harness import DeepSeekHarness
    t0 = time.time()
    try:
        with DeepSeekHarness(dsh_home='/Users/liyang/.dsh', cwd='/Users/liyang/Documents/CMAWSE-REBUILD',
                             provider='deepseek-account', model='deepseek-flash',
                             request_timeout_seconds=120) as h:
            record['route'] = 'deepseek-account/deepseek-flash'
            result = h.run(prompt, session_id='p8-cmawse-sdk-' + str(int(time.time())))
            record['elapsed_s'] = round(time.time() - t0, 1)
            record['final_response'] = result.final_response
            record['finish_reason'] = result.finish_reason
            record['status'] = 'OK' if result.finish_reason not in ('error',) else f'ERROR({result.finish_reason})'
            # 失败事件中的 LlmError 结构（脱敏：仅 code/message，无凭据）
            for ev in getattr(result, 'events', []):
                if ev.get('type') == 'turn/end':
                    record['turn_end_reason'] = json.dumps(ev.get('data', {}).get('reason', {}), ensure_ascii=False, default=str)[:400]
    except Exception as e:
        record['elapsed_s'] = round(time.time() - t0, 1)
        record['status'] = 'ERROR'
        record['error_type'] = type(e).__name__
        record['error'] = str(e)[:2000]
    json.dump(record, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1, default=str)
    print(json.dumps({k: v for k, v in record.items() if k != 'final_response'}, ensure_ascii=False, default=str))
    if 'final_response' in record:
        print('RESPONSE:', record['final_response'][:400])

if __name__ == '__main__':
    main()
