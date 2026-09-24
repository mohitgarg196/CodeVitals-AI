def format_report(results):
    detection = results["detection_metrics"]
    consistency = results["consistency_metrics"]
    performance = results["performance_metrics"]

    lines = [
        "========== CODEVITALS V7 EVALUATION ==========",
        "",
        "Benchmark:",
        str(results["benchmark"]),
        "",
        "Runs:",
        str(len(results["runs"])),
        "",
        "Detection (pooled across runs):",
        f"Expected findings per run : {results['expected_finding_count']}",
        f"Expected run-cases        : {detection['expected_run_cases']}",
        f"True positives    : {detection['true_positives']}",
        f"False positives   : {detection['false_positives']}",
        f"False negatives   : {detection['false_negatives']}",
        "",
        f"Precision: {detection['precision']:.4f}",
        f"Recall:    {detection['recall']:.4f}",
        f"F1:        {detection['f1_score']:.4f}",
        "",
        "Repeated-run finding-set consistency:",
    ]
    for item in consistency["pairwise_jaccard"]:
        lines.append(
            f"{item['run_a']} vs {item['run_b']} : "
            f"{item['jaccard_similarity']:.4f}"
        )
    lines.extend([
        f"Average consistency: {consistency['average_consistency']:.4f}",
        "",
        "Performance:",
        f"Avg latency      : {performance['average_latency']:.2f}s",
        f"Min latency      : {performance['min_latency']:.2f}s",
        f"Max latency      : {performance['max_latency']:.2f}s",
        f"Avg tool calls   : {performance['average_tool_calls']:.2f}",
        f"Avg total tokens : {performance['average_total_tokens']:.2f}",
        "",
        "Missed findings:",
    ])
    for finding in detection["missed_findings"]:
        lines.append(
            f"  - {finding.get('type', finding.get('title', 'finding'))} "
            f"in {finding.get('file', '?')}"
        )
    if not detection["missed_findings"]:
        lines.append("  (none)")
    lines.append("")
    lines.append("False positives:")
    for finding in detection["false_positive_findings"]:
        lines.append(
            f"  - {finding.get('title', finding.get('type', 'finding'))} "
            f"in {finding.get('file', '?')}"
        )
    if not detection["false_positive_findings"]:
        lines.append("  (none)")
    lines.append("")
    lines.append("===============================================")
    return "\n".join(lines)
