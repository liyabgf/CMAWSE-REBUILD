# -*- coding: utf-8 -*-
"""P5 REWRITTEN 类型校验器：Phase II 批次响应契约的显式类型/枚举边界。

与历史 llm_boundary.py（EXTRACTED, extracted/quarantine/agent__llm_boundary.py_L21193.py）
的关系：历史组件面向 Branch A（pydantic、extra=forbid、快照哈希、重复键拒止、
MindDecision 枚举）；Phase II 引擎是 callable 接口、无 pydantic、无 JSON 字符串层，
故从未接入。本组件**不是历史实现的恢复**，而是按同一防御思想为 Phase II 合同新写的
stdlib 校验器，差异逐条记录于 E2_TYPE_BOUNDARY_REPORT.md。

用法：把 agent callable 包一层；校验失败抛 TypeError/ValueError，由引擎既有的
except 分支接住 -> parsing_failures += 1 -> 默认值兜底（不修改引擎本体）。
"""
import re

VALID_STATES = {'q0', 'q1', 'q2', 'st_idle', 'st_open', 'st_locked'}
VALID_MODELS = {'M1', 'M2', 'M3'}

class BatchContractError(TypeError):
    pass

def _check_str(v, path):
    if not isinstance(v, str) or not (0 < len(v) <= 256):
        raise BatchContractError(f'{path}: expected non-empty str<=256, got {type(v).__name__}')
    return v

def _check_state(v, path):
    _check_str(v, path)
    if v not in VALID_STATES:
        raise BatchContractError(f'{path}: value not in closed state vocab: {v!r}')
    return v

def validate_batch_response(resp):
    if not isinstance(resp, dict):
        raise BatchContractError(f'batch response: expected dict, got {type(resp).__name__}')
    for k in resp:
        if not isinstance(k, str):
            raise BatchContractError(f'batch response key: expected str, got {type(k).__name__}')
    d1 = resp.get('d1_predictions', {})
    if not isinstance(d1, dict):
        raise BatchContractError(f'd1_predictions: expected dict, got {type(d1).__name__}')
    for k, v in d1.items():
        if not re.fullmatch(r'\d+', str(k)):
            raise BatchContractError(f'd1_predictions key: expected tau digits, got {k!r}')
        _check_state(v, f'd1_predictions[{k}]')
    d2 = resp.get('d2_matrix', {})
    if not isinstance(d2, dict):
        raise BatchContractError(f'd2_matrix: expected dict, got {type(d2).__name__}')
    for mk, row in d2.items():
        if mk not in VALID_MODELS:
            raise BatchContractError(f'd2_matrix model key: {mk!r} not in {sorted(VALID_MODELS)}')
        if not isinstance(row, dict):
            raise BatchContractError(f'd2_matrix[{mk}]: expected dict, got {type(row).__name__}')
        for ak, av in row.items():
            _check_str(ak, f'd2_matrix[{mk}] action key')
            _check_state(av, f'd2_matrix[{mk}][{ak}]')
    d4 = resp.get('d4_predictions', {})
    if not isinstance(d4, dict):
        raise BatchContractError(f'd4_predictions: expected dict, got {type(d4).__name__}')
    for k, v in d4.items():
        _check_str(str(k), 'd4 key')
        _check_state(v, f'd4_predictions[{k}]')
    d5 = resp.get('d5_prediction', 'INVALID')
    _check_state(d5, 'd5_prediction')
    for extra in set(resp) - {'d1_predictions', 'd2_matrix', 'd4_predictions', 'd5_prediction'}:
        raise BatchContractError(f'unexpected extra field: {extra!r}')
    return resp

def typechecked(agent_callable, rejection_log):
    def wrapped(payload):
        resp = agent_callable(payload)
        try:
            return validate_batch_response(resp) if payload.get('phase') == 'BATCH_EVALUATION' else resp
        except BatchContractError as e:
            rejection_log.append(str(e))
            raise
    return wrapped
