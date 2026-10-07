# S3 and S4 with TopstepX's fees, intraday dips and the call-up (task 15)

Sealed bars sha256 d2e4ebf90949244441d898fd9d34236eb768100ff64c298812604522b6be316b; the forward protocol's frozen S3 and S4 through research/engine.py; roll dates excluded. B5's paths (research/b5_paths.simulate): from $2,000, one Topstep 50K account at a time on TopstepX, whole micros (evaluation budget $1,000, funded $500), 365 days; development paths start every trading day and end by 2025-10-05, the benchmark is one path from 2025-10-06. Fees per micro round trip: B5 $0.50, TopstepX $1.22. Dips: the loss limit is checked at each trade's worst excursion (the exit bar's whole range included, the fee charged up front). Call-up: every account closes at the path's 3rd payout request and the Live account counts for nothing. Sizing includes the fee in each variant's budget (a live account must size with the real $1.22).

Which rows to read: the bracket was chosen on all development years, so 'development, in-sample' flatters both candidates. 'Development from 2021' is out of sample for the bracket (S3's walk-forward chain chose it each year from 2021 on earlier years only), and the benchmark is one path the choice never saw.

Net per evaluation is (mean final cash - $2,000) / mean evaluations bought; it includes the activations and the payouts.

| candidate | period | policy | call-up | fee | dips | paths | ruin | cash p10 | median cash | mean cash | > $2,000 | evaluations | payouts | net per evaluation |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S3 | development, in-sample | ask | none | B5 | ignored | 3625 | 0.0% | 1,620 | 4,993 | 5,384 | 88% | 15.2 | 5.5 | +222 |
| S3 | development, in-sample | ask | none | B5 | counted | 3625 | 0.0% | 1,168 | 4,097 | 4,862 | 83% | 19.5 | 5.3 | +147 |
| S3 | development, in-sample | ask | none | TopstepX | ignored | 3625 | 0.0% | 1,373 | 4,423 | 4,868 | 83% | 15.8 | 5.3 | +181 |
| S3 | development, in-sample | ask | none | TopstepX | counted | 3625 | 0.0% | 1,177 | 3,516 | 4,385 | 80% | 19.8 | 5.0 | +120 |
| S3 | development, in-sample | ask | 3rd payout | B5 | ignored | 3625 | 0.0% | 1,569 | 3,316 | 3,306 | 85% | 9.3 | 2.8 | +141 |
| S3 | development, in-sample | ask | 3rd payout | B5 | counted | 3625 | 0.0% | 1,177 | 3,214 | 3,107 | 78% | 12.4 | 2.8 | +89 |
| S3 | development, in-sample | ask | 3rd payout | TopstepX | ignored | 3625 | 0.0% | 1,424 | 3,249 | 3,152 | 79% | 9.9 | 2.8 | +116 |
| S3 | development, in-sample | ask | 3rd payout | TopstepX | counted | 3625 | 0.0% | 1,228 | 3,025 | 2,952 | 76% | 13.1 | 2.8 | +73 |
| S3 | development, in-sample | wait | none | B5 | ignored | 3625 | 0.0% | 2,124 | 5,213 | 5,778 | 90% | 13.6 | 4.5 | +278 |
| S3 | development, in-sample | wait | none | B5 | counted | 3625 | 0.0% | 1,208 | 4,593 | 5,178 | 84% | 17.0 | 4.2 | +187 |
| S3 | development, in-sample | wait | none | TopstepX | ignored | 3625 | 0.0% | 1,664 | 4,570 | 5,383 | 84% | 13.7 | 4.2 | +246 |
| S3 | development, in-sample | wait | none | TopstepX | counted | 3625 | 0.0% | 1,419 | 3,986 | 4,777 | 80% | 17.5 | 3.9 | +159 |
| S3 | development, in-sample | wait | 3rd payout | B5 | ignored | 3625 | 0.0% | 2,124 | 4,227 | 3,925 | 90% | 9.1 | 2.6 | +212 |
| S3 | development, in-sample | wait | 3rd payout | B5 | counted | 3625 | 0.0% | 1,208 | 4,161 | 3,716 | 84% | 11.6 | 2.5 | +148 |
| S3 | development, in-sample | wait | 3rd payout | TopstepX | ignored | 3625 | 0.0% | 1,664 | 4,026 | 3,765 | 84% | 9.7 | 2.5 | +181 |
| S3 | development, in-sample | wait | 3rd payout | TopstepX | counted | 3625 | 0.0% | 1,419 | 3,684 | 3,454 | 80% | 13.1 | 2.4 | +111 |
| S3 | development from 2021 | ask | none | B5 | ignored | 956 | 0.0% | 1,920 | 3,962 | 3,972 | 90% | 14.2 | 5.7 | +139 |
| S3 | development from 2021 | ask | none | B5 | counted | 956 | 0.0% | 942 | 2,749 | 3,345 | 72% | 17.8 | 5.3 | +75 |
| S3 | development from 2021 | ask | none | TopstepX | ignored | 956 | 0.0% | 1,334 | 4,020 | 3,729 | 81% | 14.6 | 5.8 | +119 |
| S3 | development from 2021 | ask | none | TopstepX | counted | 956 | 0.0% | 1,117 | 3,465 | 3,359 | 71% | 17.3 | 5.4 | +79 |
| S3 | development from 2021 | ask | 3rd payout | B5 | ignored | 956 | 0.0% | 1,471 | 2,784 | 2,826 | 84% | 7.7 | 2.9 | +108 |
| S3 | development from 2021 | ask | 3rd payout | B5 | counted | 956 | 0.0% | 1,168 | 2,478 | 2,436 | 62% | 11.3 | 2.9 | +38 |
| S3 | development from 2021 | ask | 3rd payout | TopstepX | ignored | 956 | 0.0% | 1,545 | 2,662 | 2,671 | 69% | 7.9 | 3.0 | +85 |
| S3 | development from 2021 | ask | 3rd payout | TopstepX | counted | 956 | 0.0% | 1,313 | 2,464 | 2,459 | 62% | 10.8 | 3.0 | +42 |
| S3 | development from 2021 | wait | none | B5 | ignored | 956 | 0.0% | 2,288 | 5,403 | 5,052 | 96% | 11.6 | 4.2 | +262 |
| S3 | development from 2021 | wait | none | B5 | counted | 956 | 0.0% | 1,493 | 4,580 | 4,547 | 81% | 13.7 | 3.7 | +186 |
| S3 | development from 2021 | wait | none | TopstepX | ignored | 956 | 0.0% | 2,205 | 5,386 | 4,920 | 92% | 11.0 | 4.1 | +265 |
| S3 | development from 2021 | wait | none | TopstepX | counted | 956 | 0.0% | 1,386 | 4,518 | 4,548 | 79% | 13.9 | 3.8 | +184 |
| S3 | development from 2021 | wait | 3rd payout | B5 | ignored | 956 | 0.0% | 2,288 | 4,115 | 3,927 | 96% | 7.8 | 2.8 | +248 |
| S3 | development from 2021 | wait | 3rd payout | B5 | counted | 956 | 0.0% | 1,493 | 4,215 | 3,600 | 81% | 9.8 | 2.5 | +163 |
| S3 | development from 2021 | wait | 3rd payout | TopstepX | ignored | 956 | 0.0% | 2,205 | 4,049 | 3,731 | 92% | 7.9 | 2.6 | +220 |
| S3 | development from 2021 | wait | 3rd payout | TopstepX | counted | 956 | 0.0% | 1,386 | 4,007 | 3,556 | 79% | 9.9 | 2.5 | +157 |
| S3 | benchmark | ask | none | B5 | ignored | 1 | 0.0% | 5,034 | 5,034 | 5,034 | 100% | 5.0 | 6.0 | +607 |
| S3 | benchmark | ask | none | B5 | counted | 1 | 0.0% | 2,536 | 2,536 | 2,536 | 100% | 10.0 | 4.0 | +54 |
| S3 | benchmark | ask | none | TopstepX | ignored | 1 | 0.0% | 4,977 | 4,977 | 4,977 | 100% | 8.0 | 6.0 | +372 |
| S3 | benchmark | ask | none | TopstepX | counted | 1 | 0.0% | 2,500 | 2,500 | 2,500 | 100% | 10.0 | 4.0 | +50 |
| S3 | benchmark | ask | 3rd payout | B5 | ignored | 1 | 0.0% | 3,941 | 3,941 | 3,941 | 100% | 1.0 | 3.0 | +1,941 |
| S3 | benchmark | ask | 3rd payout | B5 | counted | 1 | 0.0% | 2,672 | 2,672 | 2,672 | 100% | 7.0 | 3.0 | +96 |
| S3 | benchmark | ask | 3rd payout | TopstepX | ignored | 1 | 0.0% | 3,923 | 3,923 | 3,923 | 100% | 1.0 | 3.0 | +1,923 |
| S3 | benchmark | ask | 3rd payout | TopstepX | counted | 1 | 0.0% | 2,650 | 2,650 | 2,650 | 100% | 7.0 | 3.0 | +93 |
| S3 | benchmark | wait | none | B5 | ignored | 1 | 0.0% | 3,915 | 3,915 | 3,915 | 100% | 8.0 | 3.0 | +239 |
| S3 | benchmark | wait | none | B5 | counted | 1 | 0.0% | 3,839 | 3,839 | 3,839 | 100% | 7.0 | 3.0 | +263 |
| S3 | benchmark | wait | none | TopstepX | ignored | 1 | 0.0% | 3,893 | 3,893 | 3,893 | 100% | 8.0 | 3.0 | +237 |
| S3 | benchmark | wait | none | TopstepX | counted | 1 | 0.0% | 3,820 | 3,820 | 3,820 | 100% | 7.0 | 3.0 | +260 |
| S3 | benchmark | wait | 3rd payout | B5 | ignored | 1 | 0.0% | 4,456 | 4,456 | 4,456 | 100% | 3.0 | 3.0 | +819 |
| S3 | benchmark | wait | 3rd payout | B5 | counted | 1 | 0.0% | 4,086 | 4,086 | 4,086 | 100% | 5.0 | 3.0 | +417 |
| S3 | benchmark | wait | 3rd payout | TopstepX | ignored | 1 | 0.0% | 4,434 | 4,434 | 4,434 | 100% | 3.0 | 3.0 | +811 |
| S3 | benchmark | wait | 3rd payout | TopstepX | counted | 1 | 0.0% | 4,067 | 4,067 | 4,067 | 100% | 5.0 | 3.0 | +413 |
| S4 | development, in-sample | ask | none | B5 | ignored | 3625 | 1.8% | 1,016 | 4,441 | 5,116 | 81% | 18.6 | 5.3 | +168 |
| S4 | development, in-sample | ask | none | B5 | counted | 3625 | 5.9% | 488 | 3,367 | 4,420 | 74% | 23.2 | 4.5 | +104 |
| S4 | development, in-sample | ask | none | TopstepX | ignored | 3625 | 1.8% | 785 | 3,918 | 4,650 | 75% | 19.2 | 5.1 | +138 |
| S4 | development, in-sample | ask | none | TopstepX | counted | 3625 | 6.7% | 492 | 3,108 | 4,144 | 68% | 23.6 | 4.3 | +91 |
| S4 | development, in-sample | ask | 3rd payout | B5 | ignored | 3625 | 1.8% | 1,086 | 3,440 | 3,279 | 78% | 10.8 | 2.8 | +119 |
| S4 | development, in-sample | ask | 3rd payout | B5 | counted | 3625 | 5.9% | 521 | 3,066 | 3,008 | 76% | 15.2 | 2.6 | +66 |
| S4 | development, in-sample | ask | 3rd payout | TopstepX | ignored | 3625 | 1.8% | 785 | 3,253 | 3,155 | 76% | 11.8 | 2.8 | +98 |
| S4 | development, in-sample | ask | 3rd payout | TopstepX | counted | 3625 | 6.7% | 592 | 2,954 | 2,901 | 72% | 15.9 | 2.5 | +57 |
| S4 | development, in-sample | wait | none | B5 | ignored | 3625 | 4.3% | 620 | 4,932 | 5,733 | 88% | 16.6 | 4.5 | +225 |
| S4 | development, in-sample | wait | none | B5 | counted | 3625 | 6.7% | 226 | 3,438 | 4,586 | 79% | 21.7 | 3.7 | +119 |
| S4 | development, in-sample | wait | none | TopstepX | ignored | 3625 | 4.4% | 571 | 4,241 | 5,434 | 84% | 17.0 | 4.3 | +202 |
| S4 | development, in-sample | wait | none | TopstepX | counted | 3625 | 7.0% | 82 | 3,313 | 4,501 | 71% | 21.8 | 3.7 | +115 |
| S4 | development, in-sample | wait | 3rd payout | B5 | ignored | 3625 | 4.3% | 620 | 4,151 | 3,866 | 88% | 10.4 | 2.6 | +179 |
| S4 | development, in-sample | wait | 3rd payout | B5 | counted | 3625 | 6.7% | 226 | 3,685 | 3,372 | 79% | 14.9 | 2.3 | +92 |
| S4 | development, in-sample | wait | 3rd payout | TopstepX | ignored | 3625 | 4.4% | 571 | 4,034 | 3,800 | 84% | 11.2 | 2.5 | +161 |
| S4 | development, in-sample | wait | 3rd payout | TopstepX | counted | 3625 | 7.0% | 82 | 3,509 | 3,183 | 71% | 15.6 | 2.2 | +76 |
| S4 | development from 2021 | ask | none | B5 | ignored | 956 | 7.0% | 189 | 3,154 | 3,732 | 53% | 19.9 | 5.1 | +87 |
| S4 | development from 2021 | ask | none | B5 | counted | 956 | 20.7% | 30 | 2,120 | 3,399 | 51% | 24.5 | 4.0 | +57 |
| S4 | development from 2021 | ask | none | TopstepX | ignored | 956 | 7.0% | 242 | 2,502 | 3,661 | 60% | 20.5 | 5.4 | +81 |
| S4 | development from 2021 | ask | none | TopstepX | counted | 956 | 23.6% | 32 | 2,004 | 3,289 | 50% | 25.0 | 3.9 | +51 |
| S4 | development from 2021 | ask | 3rd payout | B5 | ignored | 956 | 7.0% | 366 | 1,974 | 2,345 | 46% | 13.3 | 2.8 | +26 |
| S4 | development from 2021 | ask | 3rd payout | B5 | counted | 956 | 20.7% | 30 | 1,715 | 2,192 | 46% | 18.5 | 2.3 | +10 |
| S4 | development from 2021 | ask | 3rd payout | TopstepX | ignored | 956 | 7.0% | 303 | 2,272 | 2,392 | 58% | 12.8 | 2.8 | +31 |
| S4 | development from 2021 | ask | 3rd payout | TopstepX | counted | 956 | 23.6% | 32 | 2,475 | 2,327 | 55% | 17.1 | 2.3 | +19 |
| S4 | development from 2021 | wait | none | B5 | ignored | 956 | 16.3% | 28 | 4,249 | 4,467 | 77% | 17.5 | 3.8 | +141 |
| S4 | development from 2021 | wait | none | B5 | counted | 956 | 23.6% | 30 | 2,710 | 3,580 | 60% | 23.1 | 3.0 | +68 |
| S4 | development from 2021 | wait | none | TopstepX | ignored | 956 | 16.7% | 28 | 3,980 | 4,381 | 74% | 17.8 | 3.8 | +134 |
| S4 | development from 2021 | wait | none | TopstepX | counted | 956 | 24.5% | 30 | 2,557 | 3,648 | 58% | 23.3 | 3.4 | +71 |
| S4 | development from 2021 | wait | 3rd payout | B5 | ignored | 956 | 16.3% | 28 | 4,197 | 3,349 | 77% | 11.3 | 2.3 | +119 |
| S4 | development from 2021 | wait | 3rd payout | B5 | counted | 956 | 23.6% | 30 | 3,685 | 2,790 | 60% | 17.0 | 2.0 | +46 |
| S4 | development from 2021 | wait | 3rd payout | TopstepX | ignored | 956 | 16.7% | 28 | 4,105 | 3,271 | 74% | 11.6 | 2.3 | +109 |
| S4 | development from 2021 | wait | 3rd payout | TopstepX | counted | 956 | 24.5% | 30 | 3,558 | 2,701 | 58% | 17.3 | 2.0 | +41 |
| S4 | benchmark | ask | none | B5 | ignored | 1 | 0.0% | 4,947 | 4,947 | 4,947 | 100% | 20.0 | 6.0 | +147 |
| S4 | benchmark | ask | none | B5 | counted | 1 | 0.0% | 1,234 | 1,234 | 1,234 | 0% | 26.0 | 3.0 | -29 |
| S4 | benchmark | ask | none | TopstepX | ignored | 1 | 0.0% | 4,798 | 4,798 | 4,798 | 100% | 20.0 | 6.0 | +140 |
| S4 | benchmark | ask | none | TopstepX | counted | 1 | 0.0% | 1,147 | 1,147 | 1,147 | 0% | 27.0 | 3.0 | -32 |
| S4 | benchmark | ask | 3rd payout | B5 | ignored | 1 | 0.0% | 5,052 | 5,052 | 5,052 | 100% | 2.0 | 3.0 | +1,526 |
| S4 | benchmark | ask | 3rd payout | B5 | counted | 1 | 0.0% | 1,234 | 1,234 | 1,234 | 0% | 26.0 | 3.0 | -29 |
| S4 | benchmark | ask | 3rd payout | TopstepX | ignored | 1 | 0.0% | 4,964 | 4,964 | 4,964 | 100% | 2.0 | 3.0 | +1,482 |
| S4 | benchmark | ask | 3rd payout | TopstepX | counted | 1 | 0.0% | 1,147 | 1,147 | 1,147 | 0% | 27.0 | 3.0 | -32 |
| S4 | benchmark | wait | none | B5 | ignored | 1 | 0.0% | 2,032 | 2,032 | 2,032 | 100% | 21.0 | 2.0 | +2 |
| S4 | benchmark | wait | none | B5 | counted | 1 | 0.0% | 1,787 | 1,787 | 1,787 | 0% | 26.0 | 2.0 | -8 |
| S4 | benchmark | wait | none | TopstepX | ignored | 1 | 0.0% | 2,010 | 2,010 | 2,010 | 100% | 21.0 | 2.0 | +0 |
| S4 | benchmark | wait | none | TopstepX | counted | 1 | 0.0% | 1,716 | 1,716 | 1,716 | 0% | 27.0 | 2.0 | -11 |
| S4 | benchmark | wait | 3rd payout | B5 | ignored | 1 | 0.0% | 2,032 | 2,032 | 2,032 | 100% | 21.0 | 2.0 | +2 |
| S4 | benchmark | wait | 3rd payout | B5 | counted | 1 | 0.0% | 1,787 | 1,787 | 1,787 | 0% | 26.0 | 2.0 | -8 |
| S4 | benchmark | wait | 3rd payout | TopstepX | ignored | 1 | 0.0% | 2,010 | 2,010 | 2,010 | 100% | 21.0 | 2.0 | +0 |
| S4 | benchmark | wait | 3rd payout | TopstepX | counted | 1 | 0.0% | 1,716 | 1,716 | 1,716 | 0% | 27.0 | 2.0 | -11 |
