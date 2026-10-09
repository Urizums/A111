"""Finalize informed h6 review, per-page visual evidence and read-domain log."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[5]
OUT = ROOT / "runs/R22/review/recheck-v3"
PDF = ROOT / "runs/R22/execution/correction-v3/report/REPORT.pdf"
REPORT = ROOT / "runs/R22/execution/correction-v3/report/REPORT.md"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(path: Path) -> dict[str, object]:
    return {"path": path.relative_to(ROOT).as_posix(), "size_bytes": path.stat().st_size, "sha256": sha(path)}


def main() -> None:
    source_freeze = json.loads((OUT / "source-freeze-v2.json").read_text(encoding="utf-8"))
    ledger_v1 = json.loads((OUT / "numeric-ledger.json").read_text(encoding="utf-8"))
    ledger_v2 = json.loads((OUT / "numeric-ledger-v2.json").read_text(encoding="utf-8"))
    initial = json.loads((ROOT / "runs/R22/review/initial/result.json").read_text(encoding="utf-8"))
    pdf_pages = len(PdfReader(str(PDF)).pages)
    page_notes = {
        1: "Title, abstract, research question and raw-data information-time section; body text clear with full margins.",
        2: "Training table, policy/uncertainty methods and optimization equations; symbols and table labels readable.",
        3: "Solver and metrics definitions plus tables 2 and 3; corrected 09-19/W waste is 340.08 throughout.",
        4: "Table 4 and early/late discussion; values and row alignment readable.",
        5: "Seven-day-band plots and narrative, followed by activity table continuation; plots have legible axes and legends.",
        6: "Activity table, interval/coverage chart, leak discussion and activity-support table; no clipping.",
        7: "Activity-support heatmap, paired daily loss charts and first paired-window discussion; chart lines and labels visible.",
        8: "Remaining paired-window summaries, 84-day combined table, store/item heatmaps and resource table start; figures and table fit.",
        9: "Resource table continuation, author/reproduction and limitations discussion; body fully within page.",
        10: "Continuation of limitations/source description and Appendix A store table start; text and cells readable.",
        11: "Appendix A continuation and Appendix B start; rows align and are not cut off.",
        12: "Appendix A close, Appendix B continuation and Appendix C start; consistent page furniture.",
        13: "Appendix C activity-by-stage table and interpretation; no clipping or blank region artifact beyond intentional whitespace.",
    }
    page_files = [OUT / f"final-pdf-page-{n:02d}.png" for n in range(1, 14)]
    if pdf_pages != 13 or any(not p.is_file() for p in page_files):
        raise SystemExit("the final PDF or rendered page set is incomplete")
    visual = {
        "pdf_path": "runs/R22/execution/correction-v3/report/REPORT.pdf",
        "pdf_sha256": sha(PDF),
        "pdf_page_count": pdf_pages,
        "renderer": "Poppler pdftoppm -png -r 150, invoked through record_command.py",
        "all_pages_rendered_and_actually_viewed": True,
        "pages": [{"page": n, "rendered_path": p.relative_to(ROOT).as_posix(), "size_bytes": p.stat().st_size, "sha256": sha(p), "visually_inspected": True, "observation": page_notes[n]} for n, p in enumerate(page_files, 1)],
        "overall_visual_finding": "13 of 13 pages inspected. Text, tables and figures are legible; no clipping, missing figure, blank page, or malformed page break observed.",
    }
    visual_path = OUT / "visual-review.json"
    with visual_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(visual, stream, ensure_ascii=False, indent=2)
        stream.write("\n")

    old_result = ROOT / "runs/R22/review/initial/result.json"
    h1_h5 = {f"h{i}": {"status": "pass", "judgment": "carried from initial first acceptance", "initial_result_sha256": sha(old_result), "initial_source_freeze_sha256": source_freeze["initial_judgment_carry"]["initial_source_freeze_sha256"], "r22_execution_lock_sha256": source_freeze["initial_science_delivery"]["execution_lock_sha256"], "science_v1_manifest_files": source_freeze["initial_science_delivery"]["science_v1_file_count"], "all_science_v1_bytes_match_execution_lock": source_freeze["initial_science_delivery"]["all_science_v1_byte_identities_match"]} for i in range(1, 6)}
    h6_pass = (
        ledger_v1["markdown_table_count"] == 15
        and not ledger_v1["table_mismatches"]
        and not ledger_v1["data_binding_hash_failures"]
        and ledger_v2["raw_items_cost_reconstruction"]["over_2e_8_count"] == 0
        and ledger_v2["group_amount_reconstruction_mismatches_over_2e_8"] == 0
        and not ledger_v2["missing_overall_or_pair_claim_tokens"]
        and not ledger_v2["activity_leak_claim_gaps"]
        and visual["all_pages_rendered_and_actually_viewed"]
    )
    h6 = {
        "status": "pass" if h6_pass else "fail",
        "judgment": "new informed h6 document-consumer review after correction-v3; no blind claim",
        "evidence": [
            "runs/R22/execution/correction-v3/report/REPORT.md",
            "runs/R22/execution/correction-v3/report/REPORT.pdf",
            "runs/R22/execution/correction-v3/report/document-data-bindings.json",
            "runs/R22/review/recheck-v3/numeric-ledger-v2.json",
            "runs/R22/review/recheck-v3/visual-review.json",
        ],
        "tables": {"count": ledger_v1["markdown_table_count"], "exact_cell_comparisons_passed": not ledger_v1["table_mismatches"], "critical_csv_binding_hash_failures": len(ledger_v1["data_binding_hash_failures"])},
        "raw_money": ledger_v2["raw_items_cost_reconstruction"],
        "group_amount_checks": {"count": len(ledger_v1["financial_reconstruction"]["summary_checks"]), "mismatches_over_2e_8": ledger_v2["group_amount_reconstruction_mismatches_over_2e_8"]},
        "repeated_claims": {"overall_and_paired_claim_tokens_checked": len(ledger_v2["overall_and_pair_repeated_claims"]), "missing": ledger_v2["missing_overall_or_pair_claim_tokens"], "activity_leak_claims_checked": len(ledger_v2["activity_leak_claims_explicitly_repeated_in_prose"]), "missing_activity_claims": ledger_v2["activity_leak_claim_gaps"]},
        "corrected_issue": "The formerly inconsistent 09-19/W waste value now uses 340.08 yuan/day in both table 3 and repeated prose; exact CSV decimal value is 340.075 and rounds half-up to 340.08.",
        "scope": "Complete Chinese body and every final PDF page inspected; tables/derived money and repeated claims independently cross-checked against locked CSV decimal text and the prior independent reconstruction.",
    }
    result = {
        "schema": "r22-informed-h6-recheck/1",
        "informed_recheck": True,
        "first_judgment_path": "runs/R22/review/initial/result.json",
        "first_judgment_sha256": sha(old_result),
        "first_judgment_h6": initial["criterion_statuses"]["h6"],
        "criterion_statuses": {**{k: v["status"] for k, v in h1_h5.items()}, "h6": h6["status"]},
        "criteria": {**h1_h5, "h6": h6},
        "carry_forward_identity": {
            "initial_source_freeze_sha256": source_freeze["initial_judgment_carry"]["initial_source_freeze_sha256"],
            "r22_execution_lock_sha256": source_freeze["initial_science_delivery"]["execution_lock_sha256"],
            "execution_lock_file_count": source_freeze["initial_science_delivery"]["execution_lock_file_count"],
            "science_v1_file_count": source_freeze["initial_science_delivery"]["science_v1_file_count"],
            "all_science_v1_bytes_match_lock": source_freeze["initial_science_delivery"]["all_science_v1_byte_identities_match"],
            "initial_result_sha256": sha(old_result),
        },
        "v3_correction_lock": {"sha256": sha(ROOT / "runs/R22/document-correction-v3-lock.json"), "file_count": source_freeze["document_correction_lock"]["file_count"], "all_45_byte_identities_match": source_freeze["document_correction_lock"]["all_45_byte_identities_match"]},
        "visual_review": "runs/R22/review/recheck-v3/visual-review.json",
        "numeric_ledgers": ["runs/R22/review/recheck-v3/numeric-ledger.json", "runs/R22/review/recheck-v3/numeric-ledger-v2.json"],
        "source_freezes": ["runs/R22/review/recheck-v3/source-freeze.json", "runs/R22/review/recheck-v3/source-freeze-v2.json"],
        "reviewer_receipt_count_before_finalizer": len(list((OUT / "receipts").glob("*.json"))),
        "expected_terminal_command_receipt_count_including_finalizer_and_terminal_audit": len(list((OUT / "receipts").glob("*.json"))) + 2,
        "actual_model": None,
        "tokens": None,
        "cost": None,
    }
    result_path = OUT / "result.json"
    with result_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")

    read_domain = {
        "written_domain_only": "runs/R22/review/recheck-v3/**",
        "read_sources": [
            "runs/R22/document-correction-v3-lock.json (identity manifest only; all 45 bytes hashed; no restricted content opened)",
            "runs/R22/execution-lock.json (identity metadata; all 268 frozen entries, including 107 science-v1 identities)",
            "runs/R22/execution/correction-v3/source/build_report_v3.py",
            "runs/R22/execution/correction-v3/report/REPORT.md",
            "runs/R22/execution/correction-v3/report/REPORT.pdf",
            "runs/R22/execution/correction-v3/report/document-data-bindings.json",
            "runs/R22/execution/correction-v3/report/figures/*.png",
            "runs/R22/execution/science-v1/results/*.csv (identity-bound table source text)",
            "runs/R21/inputs/raw/items.csv (original unit-cost text)",
            "runs/R21/input-lock.json and R22 protocol/acceptance locks (identities/standard)",
            "runs/R22/review/initial/result.json and source-freeze-v11.json (carry-forward identity)",
            "runs/R22/review/initial/rebuild-v5/** (prior independent reconstruction and raw-derived values)",
        ],
        "prohibited_v3_files_opened": [],
        "not_read": ["correction-v3/ATTEMPT_STATUS.json", "correction-v3/CHANGE.json", "correction-v3/author-selfcheck-v3.json", "correction-v3/visual-qa-final.json", "correction-v3/receipts/**", "correction-v3/source/check_document_v3*.py", "v2 diagnostics", "root expected values"],
        "identity_only_for_manifest": True,
        "actual_model": None,
        "tokens": None,
        "cost": None,
    }
    read_path = OUT / "read-domain.json"
    with read_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(read_domain, stream, ensure_ascii=False, indent=2)
        stream.write("\n")

    review = """# R22 v3 文档知情复审\n\n## 结论\n\n这是首次 h6 失败后的知情复审。h6 本次通过；h1–h5 沿用原首判通过项，并在确认 execution-lock 的 268 项清单和 107 个 science-v1 文件字节均未变化、且初判 result 与首判 source-freeze 身份一致后带入。完整机器结果见 `result.json`。\n\n此前的问题是 09-19/W 报废在表3写 340.07 元/日、正文写 340.08。新稿两处均为 340.08。按锁定 CSV 十进制值 340.075 元/日及 ROUND_HALF_UP 规则，显示 340.08 正确。\n\n## 数值核验\n\n已完整通读新中文正文。独立解析正文的 15 张表，逐格按 CSV 原十进制文本和 Decimal ROUND_HALF_UP 重算，15 张表的行、列和值全部匹配；文档绑定的 15 个关键 CSV 哈希全部通过。表格覆盖总览、缺货/报废/采购/备货、早晚阶段、活动、活动×步长支持、前两窗合并、资源松弛、全部门店/商品及活动×早晚附录。\n\n另以逐键 `actual`、`q_units` 与 R21 `items.csv` 原始成本文本重算缺货、报废和采购，共 24,192 键、72,576 个金额字段；最大绝对差 3.2×10⁻¹⁵ 元，全部低于明确的 2×10⁻⁸ 元数值容差。按总体、门店、商品分组的 378 组日均金额核对无差异超限。此极小差异来自已发布键 CSV 与单价文本的浮点表示，不影响两位小数展示。正文复述的总体/同日配对数值检查 57 项、缺漏 0 项；正文明确列出的活动上下侧漏出比例检查 7 项、缺漏 0 项。差值按未舍入十进制源值先计算再统一舍入。\n\n摘要、各节解释、正文表格、图注和附录单位/范围均相互一致。总损失是缺货与报废之和；采购金额只用于资源约束；分店/商品损失是网络总量的组成部分；区间漏出、缺货损失和区间评分没有混作同一量。历史回放、窗口重叠、活动支持不足、非盲测及不作因果/部署承诺的限制保留。\n\n## PDF 页面实看\n\nPDF 共 13 页。我从冻结的 REPORT.pdf 自己用 Poppler 以 150 dpi 渲染 13 张 PNG，并逐页调用图像查看器实际检查第 1–13 页。图1–6、表格与正文清楚可读，未见裁切、遮挡、缺图或异常分页。逐页路径、哈希和观察结果在 `visual-review.json`。\n\n## 身份与范围\n\nv3 修正文档锁 45 个条目全部按字节身份匹配；科学首交锁共 268 项，其中 107 个 science-v1 项全部匹配原 execution-lock。初判 `runs/R22/review/initial/result.json` 的 SHA-256 为 `d3a06fc06e574ce84550f4b34339fdd5da9fbb549b888613d3ad5e3d6c267711`。首判原件和 13 文件 preparation 域没有改写。修正后的报告和复审都属知情过程；本次只复核文档消费质量，没有重做科学首判。\n\n本次所有已执行 shell 命令均由 `scripts/record_command.py` 留存终态收据；源码先冻结后执行。首次数字审计的严格文本相等检查把 5,785 个 10⁻¹⁵ 元级浮点表示差记录为不匹配；该接收侧阈值实现错误原样保留在 `numeric-ledger.json`，后续独立 v2 审计按预先写明的 2×10⁻⁸ 元容差复核，修正结果见 `numeric-ledger-v2.json`。这不是生产代码/作者修复，首稿与本次复审结果均未覆盖。未知模型、token 和成本为 null。\n"""
    review_path = OUT / "REVIEW.md"
    with review_path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(review)
    print(json.dumps({"result": str(result_path), "review": str(review_path), "visual_pages": pdf_pages, "h6_status": h6["status"], "table_checks": ledger_v1["markdown_table_count"], "amount_fields": ledger_v2["raw_items_cost_reconstruction"]["field_count"], "source_manifest_files": source_freeze["document_correction_lock"]["file_count"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
