# From Formula Generation to Platform Evaluation: A Programmatic Approach to Equity Alpha Discovery

**PUBLIC DISPLAY ADAPTATION - candidate expressions, Alpha IDs, individual platform metrics and private evidence references withheld. Original research conclusions and aggregate counts preserved. Public-release permission remains subject to the author's applicable agreements.**

**Qidian (Martin) Xing**  
UCLA Anderson · Master of Financial Engineering  
**Research results as of October 7, 2026**

## Abstract

An economically plausible trading idea need not produce strong historical returns. Even the same idea can behave differently when its data or calculation changes. This study examines a search-first approach to equity alpha discovery: a program combines market and accounting inputs under a limited set of mathematical rules, a local backtesting system evaluates the resulting formulas consistently, and selected candidates are tested on WorldQuant BRAIN. Economic interpretation then helps identify questions for further research.

The study generated and locally evaluated 20,000 formulas. Reviews of data availability, performance, platform implementation, and redundant information retained 3,285 candidates, all of which obtained valid platform results. Of these, 82 passed the recorded requirements for performance, trading, and portfolio construction: all applicable non-correlation checks. Similarity to existing alphas and final submission eligibility require separate assessment. Candidates with earlier local priority generally passed more often, although later candidates also produced discoveries. Programmatic search and local screening therefore provided a useful testing order and a catalog supported by actual platform evidence. Economic mechanisms and future investment value remain to be established.

## 1. Research Motivation

Equity factor research often begins with an economic argument: stocks that have fallen unusually far may rebound, or firms with stronger earnings quality may be valued more favorably. A reasonable argument, however, does not guarantee that a particular implementation performs well. The chosen data, historical window, combination of measures, and even the sign of a signal can change the result. Manually proposing, calculating, and recording thousands of variants is difficult and can direct attention toward successful examples.

We therefore specify a limited, transparent formula language and let a program generate candidates before applying common evaluation rules. An alpha here begins as a formula that assigns each stock a score. The researcher chooses the available inputs, operations, and windows; the program explores their combinations. This division of work permits broad comparison while preserving the origin of each formula and its unsuccessful results.

Generation alone does not tell us which formulas deserve testing resources on the target platform. We built a local backtesting system so every candidate could first be evaluated with consistent data, positions, and return rules. Screening then removes candidates with insufficient data, weak performance, or clearly redundant information. BRAIN subsequently evaluates retained formulas using its own data and rules. This sequence supports large-scale comparison and tests whether a formula remains useful outside its original computational environment.

The analysis must also look beyond scores and pass counts. We need to understand what promising formulas compare and why those comparisons might relate to stock returns. Such explanations motivate further tests rather than establish causal mechanisms. The paper asks whether the process finds candidates meeting the platform's main requirements, whether local priority helps find them earlier, and what differences between local and platform results suggest for future research.

![Figure 1. Research workflow and completed-cohort counts.](workflow.png)

## 2. Data and Information Timing

A backtest must first identify which company issued a stock at a historical date. Tickers change, and a company may issue multiple securities; connecting past reports through today's ticker can attach accounts to the wrong stock. We use daily U.S. equity market data from CRSP and annual company accounts from Compustat. CRSP's permanent security identifier, PERMNO, identifies the stock; Compustat's company identifier, GVKEY, identifies the reporting entity. Dated company–security links connect the two through the CRSP/Compustat Merged, or CCM, database.[2]

Universe membership must also reflect the past. Using only companies that exist today would omit stocks that later delisted or disappeared. At the last available market trading date of each month, the local system ranks eligible security types and exchanges by observable positive market capitalization and selects the largest 3,000 stocks. The list takes effect the following month, so information known only at month-end cannot determine earlier positions. This is a locally reconstructed universe; BRAIN's TOP3000 follows the platform's own selection rules.

Accounting data pose a further timing problem: the end of a fiscal year is usually earlier than the release of the annual report. We add 180 calendar days to the fiscal period-end field, `datadate`, to determine when a report may enter a signal. Before that date it is unavailable; afterward the latest available report is carried forward. If the signal date is more than 730 days after the original fiscal period-end, its accounting fields become missing. The 730-day clock starts at period-end, not at the date shifted by 180 days. These rules define the study's approximation to information availability.

The evaluation panel contains 15 fields, of which 12 enter the main generator. Alongside returns, volume, and capitalization are measures of profitability, valuation, cash flow, and the balance sheet. Denominators matter: net income divided by assets measures asset profitability, whereas net income divided by market capitalization compares earnings with market valuation. Capitalization is constructed from absolute closing price and shares outstanding, with monetary units aligned to the accounts. Accounting ratios require valid positive denominators; negative earnings and cash flow remain possible, while missing required debt components are not replaced with zero. Table 1 summarizes the inputs; complete definitions appear in the electronic methods supplement.[3]

**Table 1. What the main inputs compare**

| Input category | Representative calculations | What must be checked |
|---|---|---|
| Trading and company size | Stock returns, volume, capitalization | Returns including and excluding distributions differ; capitalization units must agree |
| Profitability and valuation | Net income/assets, net income/capitalization, book equity/capitalization | Different denominators answer different questions; reports must be available at the signal date |
| Operations and balance sheet | Sales/assets, operating cash flow/assets, debt/assets, cash/assets | Carried-forward annual reports can become stale; missing components are not zero |

Final local evaluation covers 2019–2024, with earlier market records supporting historical windows and membership. Positions form at the close of day t using signals available through the previous market day, t−1, and are held to the next market close. Both the holding date and return endpoint must fall inside the reporting period. A held stock's return remains in the portfolio even if it leaves the next day's universe. This sequence defines how a formula's score becomes investment performance.

## 3. Formula Generation and Local Evaluation

### 3.1 Combining Inputs, Operations, and Windows

A generic teaching expression, `rank(ts_mean(returns,5))`, computes a stock's average daily return over five observations and then ranks those averages across currently eligible stocks. Inputs, operators and windows are recorded separately. This illustrative expression is not presented as a published platform candidate. Cross-sectional ranking compares stocks on one date; time-series ranking compares one stock with its own history.

The program combines formulas under limits on depth, operation count, and distinct fields, preventing expressions from becoming arbitrarily large. An expression tree records the calculation order, with data at the leaves and operations above them. A fixed random seed, 20260930, makes generation reproducible under the same settings. Structural checks also remove repeated forms: swapping the inputs of an operation that allows this, such as addition, does not create a new formula. The search made 23,697 attempts, including 3,697 structural duplicates, and produced 20,000 structurally unique main formulas. Exact complexity limits remain in the supplement.

Candidates include transformations of one field, combinations of two measures, conditional rules, and variants of reference templates. A small implemented subset of public Alpha101 examples provided comparison and inspiration,[1] rather than a validated source for every formula. Structural uniqueness also does not imply independent economic information: different expressions may favor the same stocks. The program did not repeatedly learn new parent formulas from this round's high backtest scores; it generated candidates for subsequent common evaluation and screening.

### 3.2 Turning Stock Scores into Positions

A formula tells us which stocks it favors, but not how much to buy or sell. The signal is each stock's score; the weight is its allocated long or short position; the return is the resulting profit or loss. Consequently, the same scoring formula can earn different returns under different position rules.

We retain two local portfolios to examine the effects of scoring and position construction. The first ranks stocks on each date and subtracts the overall mean rank, forming long and short scores from the rank differences. The second smooths the previous four observations with weights 4:3:2:1, subtracts industry-average scores, ranks stocks, and removes industry-average rank differences again. Industry adjustment reduces the extent to which a score merely reflects differences between industries. Local groups use two-digit Standard Industrial Classification, or SIC2; the platform's Subindustry uses a different classification. The second portfolio brings selected operations closer to the target platform without reproducing it exactly.

Position size must then be standardized so a formula does not take more risk merely because its scores are numerically larger. Let \(U_t\) contain eligible stocks with supported signals, and let \(s_{i,t}\) be the processed score with its direction fixed. Target weights are:

$$ w_{i,t}=\frac{2s_{i,t}}{\sum_{j\in U_t}|s_{j,t}|},\qquad \sum_i|w_{i,t}|=2,\qquad \sum_iw_{i,t}=0. \tag{1} $$

Equation (1) allocates positions in proportion to relative scores. Long weights sum to 1 and absolute short weights to 1, giving gross exposure of 2 and net exposure of 0. Both portfolios require each absolute stock weight to be no greater than 0.08; the second also requires zero net exposure within each industry. A date violating these constraints has undefined weights, rather than positions repaired by clipping or optimization. For a formula without a prespecified direction, its sign is selected once using only 2019–2021 local data and then fixed.

### 3.3 Returns, Missing Data, and Assumed Trading Costs

Once close-of-day t positions exist, we can measure their gain or loss at the next market close. For the nonzero holdings \(H_t\), multiply each position by that same stock's close-to-next-close return and add the contributions:

$$ R^{\mathrm{gross}}_{t+1}=\sum_{i\in H_t}w_{i,t}r_{i,t\to t+1}. \tag{2} $$

Equation (2) gives gross return before trading costs. A rising long stock contributes positively, as does a falling short stock. If any held stock lacks its corresponding next-day return, the entire portfolio return is unobservable. We neither replace the missing return with zero nor redistribute positions after learning which future returns are missing.

Evaluation also considers variability and trading frequency. The Sharpe ratio compares average daily return with daily return volatility and is annualized using 252 trading days. Maximum drawdown measures the largest decline from an earlier high in the return path. Turnover measures how much target positions change. We assume per-side trading costs of 0, 5, and 10 basis points, where one basis point is 0.01%, and subtract the cost associated with position changes to obtain net returns. This identifies sensitivity to frequent trading. Exact turnover and cost calculations, together with the valid-date support of gross and net statistics, remain in the supplement.

## 4. Candidate Screening and Platform Implementation

### 4.1 Checking Data Before Comparing Performance

A high return observed on only a few dates or stocks may be uninformative. We first check whether a formula regularly scores enough stocks, forms valid positions, and yields observable next-day returns for those holdings. Strict next-day returns must be observable on at least 95% of dates with defined positions; the other coverage thresholds are in the supplement. All 20,000 formulas completed both local evaluations. There were 19,952 regular evaluation records and 48 outcomes in which degenerate signals or portfolios prevented ordinary performance assessment. The latter are computed outcomes, not untested formulas.

With sufficient data, candidates can qualify through two routes using 2022–2024 development statistics. The cost-sensitive route requires positive mean gross return, positive mean net return at 5 basis points per side, and positive net means in at least two development years; 2,227 qualify. The gross-performance route requires positive mean gross return, positive gross Sharpe, and positive gross means in at least two development years; 10,117 qualify. This second route prevents simplified local costs from prematurely excluding formulas that may work on the target platform. The 2,227 are entirely contained within the 10,117, so the next review covers 10,117 candidates, not the sum of the two counts.

### 4.2 Why Local Computability Is Not Enough

A formula that runs on a local computer need not perform the same calculation on WorldQuant BRAIN. We ask three questions: does the platform provide data with the required definition, can it execute the required operations, and could window, timing, or missing-value rules still produce a different result? This is the platform representability review: it establishes whether a reliable platform expression is currently available.

For example, stock returns including dividends and other distributions cannot simply replace returns excluding them. Book equity divided by market capitalization also requires consistent monetary units. Some formulas need a minimum or maximum over a long history; access to a moving average does not establish access to the required extreme-value operation. Conditional formulas pose another concrete question: if the condition is missing, does the output become missing or enter a particular branch? These details determine whether the platform formula still compares the intended quantities.

Of the 10,117 reviewed formulas, 3,562 can be converted into approximate platform expressions supported by current evidence. The remaining 6,555 lack reliable implementation evidence because of such data or calculation issues. Another 9,883 of the original 20,000 did not enter this review, so their platform representability is unknown. A reliable expression being unavailable today does not establish mathematical impossibility. Expressibility on BRAIN establishes neither identical computation across systems nor successful performance checks. Keeping these distinctions clear allows further work on blocked formulas without overstating what has already run.

### 4.3 Setting Priority When Candidates Have Different Strengths

Suppose candidate A has a higher overall Sharpe but performs poorly in one year, while B has a slightly lower Sharpe and more stable annual results. Selecting solely by overall Sharpe overlooks B's advantage. We therefore compare five measures over the 2022–2024 development period: pooled gross Sharpe, median annual Sharpe, worst annual Sharpe, maximum drawdown, and local Fitness, which combines return quality, return magnitude, and turnover.

Local Fitness accounts for return magnitude and trading frequency when comparing performance. It uses the platform's functional form with locally calculated inputs:

$$ F_{\mathrm{local}}=S_{\mathrm{local}}\sqrt{\frac{|252\,\overline{R}^{\mathrm{gross}}|}{\max(\overline{T},0.125)}}. \tag{3} $$

In Equation (3), \(S_{\mathrm{local}}\) is annualized gross Sharpe; the bars denote sample means of daily gross return and target-weight turnover, both expressed as decimal proportions. The factor 252 annualizes mean daily gross return. The denominator's floor of 0.125 limits the effect of exceptionally low turnover. This measure determines local priority; it does not replace official Fitness from a BRAIN simulation.

Pareto layering orders candidates without imposing an arbitrary weighted average of the five measures. If A is at least as good as B on all five and better on at least one, A dominates B; if each has an advantage, neither is forced to be superior. Candidates dominated by none of the others form the first layer. Removing them and repeating the comparison forms the second, ultimately producing 40 layers. Smaller drawdown losses are preferred. Layers determine testing order rather than formally reject later candidates.

### 4.4 Comparing Stock Selection as Well as Portfolio Returns

Two portfolios can rise and fall together without selecting the same stocks. One may favor a particular type of company and another different names, yet both respond to common market movements. Removing duplicates solely by historical portfolio-return similarity could therefore discard distinct selection information. The final method instead compares stock scores first and actual positions next, an order called Signal-first.

Signal similarity asks whether formulas repeatedly rank the same stocks high and low. Weight similarity asks whether they hold the same stocks on the same dates with similar long and short allocations. Fixed-date score snapshots from 2019–2023 first identify potentially redundant candidates. Detailed comparisons then examine signed daily ranks on common stocks, normalized position differences, and defined dates. Opposite rankings are not merged merely because their absolute correlation is high. Testing is deferred only when selection and position evidence is sufficient and the new candidate improves none of the quality measures; insufficient evidence favors retention.

This review retains 3,285 of the 3,562 candidates and defers 277, recording the earlier representative associated with each. Deferral is reversible scheduling, not deletion or platform failure. Expressions, directions, windows, and platform settings are fixed before running retained candidates. Existing results are reused only when formula identity and settings match. The resulting platform set thus reflects quality screening while reducing tests of clearly repeated information.

## 5. Actual Platform Results and Examples

### 5.1 What Was Found and Why the Counts Declined

The study found 82 candidates passing all applicable non-correlation checks. These met the recorded requirements for performance, trading, and portfolio construction: sufficient return relative to volatility, acceptable combined return and turnover, trading frequency within the permitted range, positions without excessive concentration, and satisfactory performance in a smaller stock universe and applicable competition requirements. Correlation and formal submission are assessed separately. The seven exact check names and applicability rules are in the supplement.

The 82 come from valid platform results for all 3,285 retained candidates, a pass rate of approximately 2.50%. There are 3,237 newly obtained valid evaluations and 48 reused records for matching expressions and settings; the latter are not new simulations. Fixed settings use U.S. TOP3000, a one-day signal delay, four-period decay, and Subindustry adjustment, with the full parameter list in the supplement. Table 2 separates the reason for each reduction from its count.

**Table 2. From all local formulas to platform-check passes**

| Research stage | Count | Why this count results |
|---|---:|---|
| Generated and locally evaluated | 20,000 | Every main formula completed both local evaluations |
| Entered platform expression review | 10,117 | Qualified through gross performance; includes the 2,227 cost-route passes |
| Supported approximate platform expressions | 3,562 | 6,555 currently lack reliable implementations; 9,883 were outside this review |
| Retained for platform evaluation | 3,285 | 277 deferred on redundancy evidence, with identities preserved |
| Obtained valid platform results | 3,285 | 3,237 new results plus 48 matching historical records |
| Passed applicable non-correlation checks | 82 | 82/3,285≈2.50%; correlation and submission remain separate |

The retained set is fully evaluated, so 82 is not a provisional count from an incomplete queue. Only a small fraction of local candidates met the platform's main requirements, however. Local screening selects testing opportunities without guaranteeing success. We next examine whether it at least places more promising opportunities earlier.

### 5.2 Did Local Priority Help?

Grouping the 40 local-priority layers into six bands, earlier candidates generally passed more often. Layers 1–5 produced 24 passes among 175 results (13.71%); layers 6–10, 19/353 (5.38%); layers 11–15, 15/548 (2.74%); layers 16–20, 11/490 (2.24%); layers 21–27, 5/925 (0.54%); and layers 28–40, 8/794 (1.01%). Figure 2 displays the completed-cohort yield in those six bands and the number of observed passes in each of the 40 layers. This adaptation replaces the original candidate-order accumulation plot with layer aggregates.

![Figure 2. Completed-cohort pass rates in six priority bands and pass counts across all 40 layers. All results include exact-match historical reuse.](complete_yield.png)

The relationship is not monotonically decreasing. Layers 28–40 outperform layers 21–27, and new passes appear after some layers with none. The last observed passing layer is 33; the 139 valid results in layers 34–40 yield no passes. This describes the present candidate pool, not a permanent stopping rule for future research.

At a resource-related pause, 709 candidates remained untested. Completing them later in the frozen order added eight passes. Later tests therefore had practical value despite their generally lower yield. Local priority informs resource allocation; actual platform results determine whether a formula meets the requirements.

### 5.3 Candidate-level material withheld

The original private paper contains four explanatory cases with exact expressions, Alpha IDs and individual platform metrics. Those cases are withheld from this display adaptation pending distribution-rights review. The aggregate finding is unchanged: local cost-adjusted performance and target-platform checks can disagree, and the locally highest-ranked candidate can fail a platform requirement.

## 6. Discussion and Conclusions

The study provides three concrete answers. First, a limited set of inputs and operations can generate many evaluable stock formulas and identify 82 with evidence of passing the platform's main checks. Second, local priority improves the concentration of discoveries early in testing without eliminating later discoveries. Third, differences between local and platform calculations matter: a candidate weak after local costs may pass on BRAIN, while the locally top-ranked formula may fail. The contribution is therefore a traceable search process, a useful testing order, and a catalog for further validation.

Three limitations qualify these findings. All 2019–2024 local information was exposed during development, and early platform results influenced methodological revisions; freezing the final evaluation does not make it an independent test on wholly unseen data. Local and platform data, universes, industries, position rules, and exact dates also differ, and approximate expressions need not calculate identically. Finally, the 180-day reporting lag is a proxy, some local statistics use only fully observable dates, and simplified costs omit actual market impact, borrowing costs, and capacity. The observed performance does not yet establish future tradable profitability.

Nor do 82 records establish 82 independent alphas with final submission eligibility. Platform correlation checks examine whether alpha returns are too similar to other alphas; this differs from local comparisons of stock ranks and positions. In the saved records, 79 await correlation confirmation, two explicitly fail the platform's self-correlation check, and one passes its applicable visible checks while production correlation is not shown. Candidate-level submission records are withheld from this adaptation.[3] These are observed intermediate achievements, with independence and out-of-sample performance still to be tested.

## 7. Further Research

First, blocked formulas should be separated by the problem to solve: missing corresponding data, an operation not yet confirmed available, or different window and missing-value treatment. Missing data call for fields with matching definitions and verified units and information dates. Unsupported calculations call for small known-input tests of platform behavior. Different treatment rules require comparison of the outputs step by step. A new platform expression represents the same formula only if its mathematical meaning is preserved; otherwise it is a new candidate. The 9,883 formulas outside the present expression review can be assessed separately, while ability to run and merit for testing remain distinct questions.

Second, improve information timing and explain performance differences. Actual announcement dates and historical report versions can test whether the fixed 180-day proxy changes stock selection. Aligning securities, market dates, industry groups, and daily positions can help isolate data effects from portfolio-rule effects. Each improvement should be compared with the frozen original results to establish which problem it resolves, rather than merely whether the final score rises.

Finally, freeze candidates and evaluation rules before testing a new period unused in development, complete platform return-correlation checks, and analyze more realistic costs. These steps can establish whether discoveries persist, provide information distinct from other alphas, and remain valuable after achievable trading costs. The next stage is to turn historical evidence into more reliable investment judgments.

## References

[1] Kakushadze, Z. (2016). *101 Formulaic Alphas*. *Wilmott*, 2016(84), 72–80. https://arxiv.org/abs/1601.00991.

[2] Morningstar/CRSP. *CRSP/Compustat Merged (CCM) Database*. Official documentation on permanent security identifiers and historical company–security links. https://indexes.morningstar.com/research-data-products/crsp-compustat-merged-database. Accessed October 8, 2026.

[3] Xing, Q. (2026). Programmatic Equity Alpha Discovery: released aggregate results and local methods. See results/ and docs/ in the accompanying repository. The full private supplement contains withheld candidate-level evidence.
