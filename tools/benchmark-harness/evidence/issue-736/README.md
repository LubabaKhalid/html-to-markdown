# Issue 736 `small_html` comparison

The reported 41.2% `real-world/wikipedia/small_html.html` slowdown was a cross-CPU comparison. Two retained nightly
captures provide a quiet, matching-host comparison between v3.15.1 and current `main`:

| Evidence | v3.15.1 | Current `main` |
| --- | --- | --- |
| Workflow run | [36309121489](https://github.com/xberg-io/html-to-markdown/actions/runs/36309121489) | [37112439581](https://github.com/xberg-io/html-to-markdown/actions/runs/37112439581) |
| Commit | `649844465a3a73d8969c4d5b318cd85170716d7f` | `695ce726d09f253565b6c16e58a953c701dec60e` |
| CPU | AMD EPYC 7763, 4 logical CPUs | AMD EPYC 7763, 4 logical CPUs |
| Runner image/class | `ubuntu24` / `github-hosted` | `ubuntu24` / `github-hosted` |
| Quiet gate | Five gated checks passed; 99.56% minimum idle | Five gated checks passed; 99.70% minimum idle |
| Median | 19.2975 ms | 19.7050 ms |
| MAD | 0.1227 ms | 0.5884 ms |
| Converted bytes | 188694 | 188683 |

The current median is 2.11% slower, below the fixture's 5% policy threshold and far below the reported 41.2%.
This rules out that headline regression on the matching hosted-runner CPU. It does not attribute the remaining 2.11%
to a particular commit: the captures came from separate runner instances, and the converted output changed by 11
bytes. A commit-level attribution would require preserved binaries measured in an alternating campaign on one runner.

## Calibration campaign

Workflow run [37137737028](https://github.com/xberg-io/html-to-markdown/actions/runs/37137737028) collected 40
schema-v2 full-corpus captures from commit `695ce726d09f253565b6c16e58a953c701dec60e`. Every capture contains the
same 29 fixtures and reports the same `AMD EPYC 7763 64-Core Processor`, `ubuntu24` image, and `github-hosted`
runner class. All five gated quiet checks passed at 99.50% idle or higher.

The exact workflow artifact is retained as `raw.zip` and verified by `SHA256SUMS`. The calibration command rejected
a 39-file negative control at the missing `0040.json`, then promoted the complete campaign with
`ACCEPT_OUTPUT_CHANGE=1`; the opt-in was required because 15 converted-output sizes changed on `main` since the
previous campaign. Comparing the latest matching-CPU nightly capture against the promoted baseline scored every
fixture and passed all guardrails without `ALLOW_HOST_MISMATCH`.
