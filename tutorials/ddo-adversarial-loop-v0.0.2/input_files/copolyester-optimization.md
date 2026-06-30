<!--
Representative rendered Markdown produced by `ddo-render` from
input_files/document_data.yaml. This is the MD surface the Red Team reads in
Phase 1 (the PDF/HTML derive from the same YAML, so the critique is valid for
all formats). Exact bytes depend on the scientific_report Jinja2 template; this
is illustrative of the content the persona critiques.
-->

# Copolyester Optimization

**Author:** Example Author, DDO Tutorial Corpus
**Date:** 2026.06.29 · **Version:** 1.0.0 · **Status:** draft

## Abstract

Multi-parameter optimization of aliphatic-aromatic copolyesters for sustainable
packaging. The transition to sustainable consumer packaged goods requires
polymers that balance mechanical durability with rapid environmental
degradability. Five copolyester candidates (PX-101 through PX-105) are evaluated
by balancing solubility, synthesizability, toxicity, and ecological impact to
identify a pre-optimized blend capable of commercial scaling.

## 1. Introduction

Current petrochemical-derived packaging materials exhibit exceptional barrier
properties and high synthesis yields but persist in the environment for
centuries. While biodegradable alternatives exist, they often suffer from low
synthesizability (yield) or unacceptably high ecological footprints during
manufacturing. This study evaluates five novel copolyester blends, aiming to
maximize manufacturing yield and marine solubility while minimizing mammalian
toxicity and carbon footprint.

## 2. Materials and Methods

Candidate selection relies on a composite desirability function. We evaluate the
candidates across four primary metrics. The objective function Z is calculated
using normalized weights for each parameter:

> Z = sum_i ( w_s · S_i + w_y · Y_i − w_t · T_i − w_e · E_i )

where S_i = Water Solubility (mg/L), Y_i = Synthesizability Yield (%),
T_i = Toxicity LD50 (g/kg) measured via murine models, and E_i = Ecology Impact
(kg CO2/kg resin). For this evaluation we apply a commercially balanced weighting
scheme: w_s = 0.3, w_y = 0.4, w_t = 0.1, and w_e = 0.2.

## 3. Results

The following table summarizes the raw empirical data collected during the
Phase II trials.

| Polymer | Yield (%) | Solubility (mg/L) | LD50 (g/kg) | Ecology (kg CO2/kg) |
|---------|-----------|-------------------|-------------|---------------------|
| PX-101  | 82.0      | 45.0              | 12.5        | 4.2                 |
| PX-102  | 91.5      | 12.0              | 18.0        | 2.1                 |
| PX-103  | 64.0      | 88.0              | 5.2         | 1.8                 |
| PX-104  | 88.5      | 42.0              | 15.4        | 2.5                 |
| PX-105  | 75.0      | 60.0              | 9.8         | 2.9                 |

*Evidence: phase_ii_dataset — Phase II trial records, internal dataset.*

## 4. Discussion

Several structure-property trade-offs emerge. First, there is a distinct inverse
correlation between manufacturing yield and water solubility: PX-102 achieved the
highest yield (91.5%) but the lowest solubility (12.0 mg/L), suggesting highly
crystalline domains that resist hydrolysis, whereas PX-103 is highly amorphous
and soluble (88.0 mg/L) but suffers from poor yield (64.0%) and higher toxicity.
Second, PX-103 demonstrated the highest toxicity (lowest LD50 at 5.2 g/kg); gas
chromatography indicates this is likely due to unreacted monomer residues trapped
within the amorphous matrix. Third, applying the objective function Z, PX-104
emerges as the optimal candidate: it achieves a commercially viable yield (88.5%)
while maintaining adequate solubility (42.0 mg/L) and a low carbon footprint (2.5
kg CO2/kg).

## 5. Conclusion

Candidate PX-104 represents the most balanced copolyester for CPG applications.
We recommend advancing PX-104 to Phase III pilot plant scaling. Future work will
focus on optimizing the catalyst to push the solubility boundary of PX-104 closer
to 50.0 mg/L without sacrificing yield.
